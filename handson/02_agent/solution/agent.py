"""見込み顧客のスコアリングエージェント（LangGraph + MLflow ResponsesAgent）。

入力: 企業特性の JSON（user メッセージの本文）。対象企業の会社IDは custom_inputs.company_id で指定する
      （指定がなければ企業特性の company_id を使う）。
      custom_inputs.save_history が true のときだけ、採点の結果を Managed Agent Memory に書き込む。
出力: 本文（評価コメント＋```json```）と custom_outputs.score_result（構造化したスコア）。

グラフ:
  prepare（AI Search で類似事例を 1 回検索・Memory を読む）
    → score_axis × 6（5 観点＋関係性の補正を同時に採点。段階と点数が合わなければ 1 回だけやり直す）
    → summarize（点数は変えずに、評価コメント・次のアクション・根拠を書く）
    → assemble（合計・Tier・確からしさはプログラムで計算）
    → save_history（save_history が true のときだけ）
"""
from __future__ import annotations

import json
import operator
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Generator, TypedDict

import mlflow
from databricks_langchain import ChatDatabricks, VectorSearchRetrieverTool
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

import memory
import rubric

mlflow.langchain.autolog()

CATALOG = os.environ["HANDSON_CATALOG"]
SCHEMA = os.environ["HANDSON_SCHEMA"]
LLM_ENDPOINT = os.environ.get("HANDSON_LLM_ENDPOINT", "databricks-claude-sonnet-5")
CASE_INDEX = os.environ["HANDSON_CASE_INDEX"]  # 全員で共有する AI Search のインデックス
MEMORY_STORE = f"{CATALOG}.{SCHEMA}.agent_memory"  # Managed Agent Memory（Unity Catalog の MEMORY_STORE）

ADJUSTMENT_KEY = rubric.ADJUSTMENT_KEY
JST = timezone(timedelta(hours=9))
_JSON_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


# ---------------------------------------------------------------------------
# 小さな関数
# ---------------------------------------------------------------------------
def parse_json(text: str) -> dict:
    """LLM の出力から JSON を取り出す（```json フェンス優先、なければ最後の {...}）。"""
    text = text or ""
    m = _JSON_RE.search(text)
    raw = m.group(1) if m else None
    if not raw:
        s, e = text.rfind("{"), text.rfind("}")
        raw = text[s:e + 1] if s != -1 and e > s else None
    try:
        return json.loads(raw) if raw else {"parse_error": True}
    except json.JSONDecodeError:
        return {"parse_error": True}


def text_of(content) -> str:
    """LLM の応答の content から本文だけを取り出す（推論ブロック付きの応答にも対応）。"""
    if isinstance(content, list):
        return "".join(c.get("text", "") for c in content
                       if isinstance(c, dict) and c.get("type") in ("text", "output_text"))
    if isinstance(content, str):
        s = content.lstrip()
        if s.startswith("[") and '"reasoning"' in s:
            try:
                return text_of(json.loads(s))
            except json.JSONDecodeError:
                return ""
        return content
    return ""


def characteristics_of(text: str) -> dict:
    s, e = (text or "").find("{"), (text or "").rfind("}")
    if s == -1 or e <= s:
        return {}
    try:
        d = json.loads(text[s:e + 1])
        return d if isinstance(d, dict) else {}
    except json.JSONDecodeError:
        return {}


def today() -> str:
    """期間の判断（12 か月以内など）の基準日。LLM は今日の日付を知らないため入力で渡す。"""
    return datetime.now(JST).date().isoformat()


# ---------------------------------------------------------------------------
# グラフの状態
# ---------------------------------------------------------------------------
class State(TypedDict, total=False):
    company_id: str
    text: str                 # 企業特性（入力の本文そのまま）
    save_history: bool
    cases: str                # AI Search で見つけた類似事例
    mem: dict                 # Memory から読んだ内容（rules / note / axis_rules）
    results: Annotated[dict, operator.or_]   # 観点ごとの採点結果（並列ノードの出力をまとめる）
    summary_text: str
    summary: dict
    score_result: dict


class AxisTask(TypedDict):
    key: str
    state: State


_llm = None
_case_tool = None


def llm():
    global _llm
    if _llm is None:
        _llm = ChatDatabricks(endpoint=LLM_ENDPOINT)
    return _llm


def case_tool():
    global _case_tool
    if _case_tool is None:
        _case_tool = VectorSearchRetrieverTool(
            index_name=CASE_INDEX, num_results=3, columns=["case_id", "title", "content"],
            tool_name="search_reference_cases", tool_description="過去の受注事例を検索する。")
    return _case_tool


def case_query(ch: dict, text: str) -> str:
    """類似事例の検索語（業種・要約・きっかけ・根拠の事実から作る）。"""
    parts = [ch.get("industry"), ch.get("summary"), ch.get("recent_trigger")]
    parts += [f for f in (ch.get("key_facts") or []) if isinstance(f, str)][:3]
    return (" ".join(str(p) for p in parts if p) or text)[:1000]


# ---------------------------------------------------------------------------
# ノード
# ---------------------------------------------------------------------------
def prepare(state: State) -> dict:
    ch = characteristics_of(state["text"])
    cid = state["company_id"]
    ws = memory.client_for_request()  # Model Serving では呼び出したユーザー本人の資格情報（OBO）
    mem = {
        "rules": memory.read(ws, MEMORY_STORE, "shared"),
        "note": memory.read(ws, MEMORY_STORE, cid),
        "axis_rules": {k: memory.read(ws, MEMORY_STORE, f"rubric_{k}") for k in rubric.AXIS_KEYS},
    }
    cases = case_tool().invoke({"query": case_query(ch, state["text"])})
    return {"mem": mem, "cases": cases if isinstance(cases, str) else str(cases)}


def fan_out(state: State) -> list[Send]:
    """5 観点と関係性の補正を、それぞれ別のノード実行として同時に走らせる。"""
    return [Send("score_axis", {"key": k, "state": state}) for k in [*rubric.AXIS_KEYS, ADJUSTMENT_KEY]]


def _axis_messages(key: str, s: State) -> list[dict]:
    mem = s["mem"]
    head = [f"【対象企業】company_id: {s['company_id']}", f"【今日の日付】{today()}"]
    if key == ADJUSTMENT_KEY:
        parts = head + [f"【企業特性】\n{s['text']}"]
        if mem["note"]:
            parts.append("【Managed Agent Memory（会社別の申し送り）】\n" + mem["note"])
        return [{"role": "system", "content": rubric.adjustment_prompt()},
                {"role": "user", "content": "\n\n".join(parts)}]
    parts = head + [f"【企業特性】\n{s['text']}"]
    if s.get("cases"):
        parts.append(f"【参照事例（AI Search で見つけた過去の受注事例）】\n{s['cases']}")
    extra = [mem["rules"], mem["axis_rules"].get(key)]
    if key == "timing":
        extra.append(mem["note"])
    extra = "\n".join(x for x in extra if x)
    if extra:
        parts.append("【Managed Agent Memory（参照）】\n" + extra)
    return [{"role": "system", "content": rubric.axis_prompt(key)},
            {"role": "user", "content": "\n\n".join(parts)}]


def _problem(key: str, parsed: dict) -> str | None:
    if key == ADJUSTMENT_KEY:
        return rubric.adjustment_result_problem(parsed)
    return rubric.axis_result_problem(key, parsed)


def score_axis(task: AxisTask) -> dict:
    """1 観点を採点する。段階と点数が合わなければ、理由を伝えて 1 回だけやり直させる。"""
    key = task["key"]
    msgs = _axis_messages(key, task["state"])
    for attempt in range(2):
        text = text_of(llm().invoke(msgs).content)
        parsed = parse_json(text)
        problem = _problem(key, parsed)
        if not problem or attempt == 1:
            break
        msgs = msgs + [{"role": "assistant", "content": text},
                       {"role": "user", "content": f"出力が基準に合っていません（{problem}）。"
                                                   "段階と、その段階の範囲内の点数で、JSON だけを出し直してください。"}]
    return {"results": {key: {"parsed": parsed, "problem": problem}}}


def route_after_scoring(state: State) -> str:
    return "fail" if any(r["problem"] for r in state["results"].values()) else "summarize"


def fail(state: State) -> dict:
    errors = {k: r["problem"] for k, r in state["results"].items() if r["problem"]}
    return {"score_result": {"company_id": state["company_id"], "axis_errors": errors,
                             "rubric_version": rubric.RUBRIC_VERSION},
            "summary_text": f"観点ごとの採点が基準に合いませんでした: {errors}"}


def summarize(state: State) -> dict:
    res = state["results"]
    scored = {rubric.axis(k)[1]: res[k]["parsed"] for k in rubric.AXIS_KEYS}
    scored["関係性の補正"] = res[ADJUSTMENT_KEY]["parsed"]
    parts = [f"【対象企業】company_id: {state['company_id']}", f"【企業特性】\n{state['text']}",
             "【観点ごとの採点結果（確定）】\n" + json.dumps(scored, ensure_ascii=False)]
    if state.get("cases"):
        parts.append(f"【参照事例】\n{state['cases']}")
    if state["mem"]["note"]:
        parts.append("【Managed Agent Memory（会社別の申し送り）】\n" + state["mem"]["note"])
    reply = text_of(llm().invoke([{"role": "system", "content": rubric.SUMMARY_PROMPT},
                                  {"role": "user", "content": "\n\n".join(parts)}]).content)
    summary = parse_json(reply)
    return {"summary_text": reply, "summary": {} if summary.get("parse_error") else summary}


def assemble(state: State) -> dict:
    res = state["results"]
    axes = {k: res[k]["parsed"] for k in rubric.AXIS_KEYS}
    ch = characteristics_of(state["text"])
    sr = rubric.assemble_score_result(state["company_id"], ch.get("company_name"), axes,
                                      res[ADJUSTMENT_KEY]["parsed"], state.get("summary") or {})
    return {"score_result": sr}


def route_after_assemble(state: State) -> str:
    return "save_history" if state.get("save_history") else END


def save_history(state: State) -> dict:
    """採点の結果を、会社別の長期記憶として Memory に書き込む（次回の採点で参照される）。"""
    sr = state["score_result"]
    d = today()
    stamp = datetime.now(JST).strftime("%Y%m%d-%H%M%S")
    contents = (f"{d} の採点: {sr['score']} 点 / Tier {sr['tier']}（採点基準 {sr['rubric_version']}）。"
                f"次のアクション: {sr['next_action']} 根拠: {sr['rationale']}")
    memory.write(memory.client_for_request(), MEMORY_STORE, state["company_id"],
                 f"/memories/episodic/score_history/{stamp}.md", contents, "スコアリングの履歴")
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("prepare", prepare)
    g.add_node("score_axis", score_axis)
    g.add_node("fail", fail)
    g.add_node("summarize", summarize)
    g.add_node("assemble", assemble)
    g.add_node("save_history", save_history)
    g.add_edge(START, "prepare")
    g.add_node("collect", lambda state: {})  # 6 つの採点がそろうのを待つ（ここで 1 回だけ分岐する）
    g.add_conditional_edges("prepare", fan_out, ["score_axis"])
    g.add_edge("score_axis", "collect")
    g.add_conditional_edges("collect", route_after_scoring, ["fail", "summarize"])
    g.add_edge("fail", END)
    g.add_edge("summarize", "assemble")
    g.add_conditional_edges("assemble", route_after_assemble, ["save_history", END])
    g.add_edge("save_history", END)
    return g.compile()


# ---------------------------------------------------------------------------
# MLflow ResponsesAgent（Model Serving の入出力）
# ---------------------------------------------------------------------------
def _request_text(request: ResponsesAgentRequest) -> str:
    texts = []
    for item in request.input:
        d = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        if d.get("role", "user") != "user":
            continue
        c = d.get("content", "")
        if isinstance(c, list):
            c = "".join((x.get("text", "") or x.get("input_text", "")) if isinstance(x, dict) else str(x)
                        for x in c)
        if c:
            texts.append(c)
    return "\n".join(texts)


class ScoringAgent(ResponsesAgent):
    def __init__(self):
        self.graph = build_graph()

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        ci = request.custom_inputs or {}
        text = _request_text(request)
        # ジョブ・評価は custom_inputs で会社IDを渡す。Review App のチャットからは渡せないので、企業特性の company_id を使う
        company_id = str(ci.get("company_id") or characteristics_of(text).get("company_id") or "").strip()
        if not company_id:
            raise ValueError("会社IDがありません（custom_inputs.company_id か、企業特性の company_id を指定してください）")
        out = self.graph.invoke({"company_id": company_id, "text": text,
                                 "save_history": bool(ci.get("save_history")), "results": {}})
        sr = out["score_result"]
        comment = (out.get("summary_text") or "").split("```")[0].strip()
        message = f"{comment}\n\n```json\n{json.dumps(sr, ensure_ascii=False)}\n```"
        item = self.create_text_output_item(text=message, id=str(uuid.uuid4()))
        return ResponsesAgentResponse(output=[item], custom_outputs={"score_result": sr})

    def predict_stream(self, request: ResponsesAgentRequest) -> Generator[ResponsesAgentStreamEvent, None, None]:
        resp = self.predict(request)
        for item in resp.output:
            yield ResponsesAgentStreamEvent(type="response.output_item.done", item=item,
                                            custom_outputs=resp.custom_outputs)


AGENT = ScoringAgent()
mlflow.models.set_model(AGENT)
