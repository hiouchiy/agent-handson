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
                   "HANDSON_LLM_ENDPOINT": LLM_ENDPOINT})
mlflow.set_experiment(EXPERIMENT_PATH)  # Step 2 で作ったエクスペリメント（トレースは Delta テーブルにも同期される）

sys.path.insert(0, AGENT_DIR)
import rubric  # noqa: E402
from agent import AGENT  # noqa: E402

print("採点基準の版:", rubric.RUBRIC_VERSION, "/ エージェント:", AGENT_DIR)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 評価データセットを登録する
# MAGIC 1 件 = **入力**（企業特性）＋**期待値**（業務部門が考える、その会社の「あるべき答え」）。
# MAGIC 期待値は、どの評価データでも同じ 2 項目を書きます。
# MAGIC
# MAGIC | 期待値のキー | 書くこと |
# MAGIC |---|---|
# MAGIC | `expected_tier` | あるべき Tier（A / B / C） |
# MAGIC | `expected_points` | あるべき答えのポイント（文章の箇条書き。点数・段階・次のアクションなど、確かめたいことを書く） |

# COMMAND ----------

from mlflow.genai import datasets

rows = json.load(open("../eval_dataset.json", encoding="utf-8"))
records = [{"inputs": {"company_id": r["company_id"], "characteristics_json": r["characteristics_json"]},
            "expectations": r["expectations"]} for r in rows]

DATASET_TABLE = f"{FQ}.scoring_eval_dataset"
# eval_dataset.json を正とし、毎回作り直す（前の内容が残って混ざらないようにする）
try:
    datasets.delete_dataset(name=DATASET_TABLE)
except Exception:
    pass  # まだない
dataset = datasets.create_dataset(name=DATASET_TABLE).merge_records(records)
display(dataset.to_df())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. スコアラー
# MAGIC どの評価データにも、同じ 4 つのスコアラーを使います。
# MAGIC - **形式のチェック（コード）**: エージェントの出力が仕様どおりか（`output_schema_valid`・`axis_levels_valid`）
# MAGIC - **Tier（コード）**: あるべき Tier と同じか（`tier_matches`）
# MAGIC - **ポイント（LLM ジャッジ）**: あるべき答えのポイントを、すべて満たしているか（`meets_expected_points`）

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
    """あるべき Tier と同じか。"""
    exp = expectations["expected_tier"]
    tier = _sr(outputs).get("tier")
    return Feedback(value=tier == exp, rationale=f"結果 {tier}（{_sr(outputs).get('score')} 点）/ 期待 {exp}")


_points_judge = ExpectationsGuidelines()


@scorer
def meets_expected_points(inputs, outputs, expectations):
    """あるべき答えのポイント（expected_points）を、すべて満たしているかを LLM ジャッジで判定する。"""
    # 採点結果は JSON の文字列にして渡す（dict のままだと、ジャッジが中の項目を読めないことがあった）
    fb = _points_judge(inputs=inputs, outputs=json.dumps({"score_result": _sr(outputs)}, ensure_ascii=False),
                       expectations={"guidelines": expectations["expected_points"]})
    return Feedback(value=fb.feedback.value, rationale=fb.rationale)


SCORERS = [output_schema_valid, axis_levels_valid, tier_matches, meets_expected_points]

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
