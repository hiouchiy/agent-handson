# Databricks notebook source
# MAGIC %md
# MAGIC # Step 3 オフライン評価（模範解答）
# MAGIC 1. 評価データ（3 件）を MLflow の**評価データセット**として Unity Catalog に登録する
# MAGIC 2. スコアラー（採点の物差し）を用意する
# MAGIC 3. `mlflow.genai.evaluate` で評価し、エクスペリメントの **評価** タブで結果を見る
# MAGIC
# MAGIC 評価データは「業務部門が期待する答え」です。最初は **わざと NG が出る** ようになっています。
# MAGIC NG の原因を Genie Code で調べて直し、もう一度このノートブックを実行して全件 OK にします。

# COMMAND ----------

# MAGIC %pip install -q -r ../../requirements.txt
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import json
import os
import sys

import mlflow

dbutils.widgets.text("agent_dir", "../../02_agent/solution", "エージェントのコードがあるフォルダ")
AGENT_DIR = os.path.abspath(dbutils.widgets.get("agent_dir"))

os.environ.update({"HANDSON_CATALOG": CATALOG, "HANDSON_SCHEMA": SCHEMA, "HANDSON_CASE_INDEX": CASE_INDEX,
                   "HANDSON_LLM_ENDPOINT": LLM_ENDPOINT,
                   "MLFLOW_TRACING_SQL_WAREHOUSE_ID": WAREHOUSE_ID})
mlflow.set_experiment(EXPERIMENT_PATH)  # Step 2 で作ったエクスペリメント（トレースは Unity Catalog に入る）

sys.path.insert(0, AGENT_DIR)
import rubric  # noqa: E402
from agent import AGENT  # noqa: E402

print("採点基準の版:", rubric.RUBRIC_VERSION, "/ エージェント:", AGENT_DIR)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 評価データセットを登録する
# MAGIC 1 件 = **入力**（企業特性）＋**期待値**（業務部門が期待する答え）。期待値は件ごとに見たい観点だけを書きます。
# MAGIC
# MAGIC | 期待値のキー | 意味 |
# MAGIC |---|---|
# MAGIC | `expected_tier` | 期待する Tier |
# MAGIC | `expected_adjustment_min` / `_max` | 関係性の補正の期待する範囲 |
# MAGIC | `expected_axis_levels` | 観点ごとの期待する段階（例: `{"timing": 4}`） |
# MAGIC | `guidelines` | 文章で書いた合格条件（LLM ジャッジが判定する） |

# COMMAND ----------

from mlflow.genai import datasets

rows = json.load(open("../eval_dataset.json", encoding="utf-8"))
records = [{"inputs": {"company_id": r["company_id"], "characteristics_json": r["characteristics_json"]},
            "expectations": r["expectations"]} for r in rows]

DATASET_TABLE = f"{FQ}.scoring_eval_dataset"
try:
    dataset = datasets.get_dataset(name=DATASET_TABLE)
except Exception:
    dataset = datasets.create_dataset(name=DATASET_TABLE)
dataset = dataset.merge_records(records)
display(dataset.to_df())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. スコアラー
# MAGIC - **形式のチェック（コード）**: どの評価データにも使う。エージェントの出力が仕様どおりか
# MAGIC - **期待値との比較（コード）**: 評価データに期待値があるときだけ判定する
# MAGIC - **LLM ジャッジ**: 評価データの `guidelines`（文章の合格条件）を満たしているか

# COMMAND ----------

from mlflow.entities import Feedback
from mlflow.genai.scorers import ExpectationsGuidelines, scorer

REQUIRED = ["company_id", "score", "tier", "subscores", "relationship_adjustment", "axis_details",
            "key_signals", "matched_cases", "next_action", "confidence", "rationale"]


def _sr(outputs):
    return (outputs or {}).get("score_result") or {}


@scorer
def output_schema_valid(outputs):
    """出力に必要な項目がそろっているか（採点が基準に合わず点数が出なかった場合も NG）。"""
    sr = _sr(outputs)
    if sr.get("axis_errors"):
        return Feedback(value=False, rationale=f"観点ごとの採点が基準に合わなかった: {sr['axis_errors']}")
    missing = [k for k in REQUIRED if k not in sr]
    return Feedback(value=not missing, rationale=f"足りない項目: {missing}" if missing else "ok")


@scorer
def axis_levels_valid(outputs):
    """観点ごとの点数が、選んだ段階の点数範囲に入っているか。"""
    details = _sr(outputs).get("axis_details") or {}
    probs = [f"{k}: {p}" for k in rubric.AXIS_KEYS if (p := rubric.axis_result_problem(k, details.get(k)))]
    return Feedback(value=not probs, rationale="; ".join(probs) or "ok")


@scorer
def tier_matches(outputs, expectations):
    exp = (expectations or {}).get("expected_tier")
    if not exp:
        return None  # この評価データでは見ない
    tier = _sr(outputs).get("tier")
    return Feedback(value=tier == exp, rationale=f"結果 {tier} / 期待 {exp}（{_sr(outputs).get('score')} 点）")


@scorer
def adjustment_in_expected_range(outputs, expectations):
    lo, hi = (expectations or {}).get("expected_adjustment_min"), (expectations or {}).get("expected_adjustment_max")
    if lo is None or hi is None:
        return None
    sr = _sr(outputs)
    adj = sr.get("relationship_adjustment")
    detail = sr.get("adjustment_detail") or {}
    return Feedback(value=isinstance(adj, int) and lo <= adj <= hi,
                    rationale=f"補正 {adj}（段階 {detail.get('level')}）/ 期待 {lo}〜{hi}。根拠: {detail.get('evidence')}")


@scorer
def axis_levels_match(outputs, expectations):
    exp = (expectations or {}).get("expected_axis_levels")
    if not exp:
        return None
    details = _sr(outputs).get("axis_details") or {}
    got = {k: (details.get(k) or {}).get("level") for k in exp}
    evidence = {k: (details.get(k) or {}).get("evidence") for k in exp}
    return Feedback(value=got == exp, rationale=f"結果 {got} / 期待 {exp}。根拠: {evidence}")


_guidelines_judge = ExpectationsGuidelines()


@scorer
def meets_guidelines(inputs, outputs, expectations):
    """評価データの guidelines（文章の合格条件）を満たしているかを LLM ジャッジで判定する。"""
    guidelines = (expectations or {}).get("guidelines")
    if not guidelines:
        return None
    # 採点結果は JSON の文字列にして渡す（dict のままだと、ジャッジが中の項目を読めないことがあった）
    fb = _guidelines_judge(inputs=inputs, outputs=json.dumps({"score_result": _sr(outputs)}, ensure_ascii=False),
                           expectations={"guidelines": guidelines})
    return Feedback(value=fb.feedback.value, rationale=fb.rationale)


SCORERS = [output_schema_valid, axis_levels_valid, tier_matches, adjustment_in_expected_range,
           axis_levels_match, meets_guidelines]

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. 評価する
# MAGIC `predict_fn` は評価データの `inputs` を受け取ってエージェントを呼ぶ関数です。
# MAGIC （Step 4 でデプロイした後は、ここをエンドポイントの呼び出しに変えても同じように評価できます）

# COMMAND ----------


def predict_fn(company_id: str, characteristics_json: str) -> dict:
    resp = AGENT.predict({
        "input": [{"role": "user", "content": "次の企業特性をスコアリングしてください。\n" + characteristics_json}],
        "custom_inputs": {"company_id": company_id}})
    return {"response": resp.output[0].content[0]["text"], "score_result": resp.custom_outputs["score_result"]}


results = mlflow.genai.evaluate(data=dataset, predict_fn=predict_fn, scorers=SCORERS)
print(json.dumps(results.metrics, ensure_ascii=False, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 結果を見る
# MAGIC エクスペリメント → **評価** タブ → いま作られた評価の実行を開くと、評価データごとに OK / NG と理由が見られます。
# MAGIC 下の表は同じ内容を 1 行 1 評価データで表示したものです。

# COMMAND ----------

summary = []
for t in mlflow.search_traces(run_id=results.run_id, return_type="list"):
    row = {"trace_id": t.info.trace_id}
    for a in t.info.assessments:
        if a.feedback is not None:
            row[a.name] = a.feedback.value
    summary.append(row)
display(spark.createDataFrame([{k: str(v) for k, v in r.items()} for r in summary]))
