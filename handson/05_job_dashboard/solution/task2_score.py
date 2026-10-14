# Databricks notebook source
# MAGIC %md
# MAGIC # ジョブ タスク 2: スコアリングエージェントのエンドポイントを呼ぶ（模範解答）
# MAGIC - 入力: `company_characteristic`（タスク 1 の出力）
# MAGIC - 処理: 1 社ずつエンドポイントを呼ぶ（並列）。`save_history=true` を付けて、採点の結果を Memory に残させる
# MAGIC - 出力: `scoring_response`（エンドポイントの応答をそのまま保存。整形はタスク 3 で行う）

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import json
from concurrent.futures import ThreadPoolExecutor

from databricks.sdk import WorkspaceClient
from pyspark.sql import functions as F

w = WorkspaceClient()
rows = spark.table(f"{FQ}.company_characteristic").select("company_id", "characteristics_json").collect()


def score(row):
    try:
        resp = w.api_client.do("POST", f"/serving-endpoints/{ENDPOINT_NAME}/invocations", body={
            "input": [{"role": "user", "content": "次の企業特性をスコアリングしてください。\n" + row["characteristics_json"]}],
            "custom_inputs": {"company_id": row["company_id"], "save_history": True}})
        return (row["company_id"], json.dumps(resp.get("custom_outputs") or {}, ensure_ascii=False), None)
    except Exception as e:  # 1 社の失敗でジョブ全体を止めない（エラーを記録して次へ）
        return (row["company_id"], None, str(e)[:1000])


with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(score, rows))

(spark.createDataFrame(results, "company_id string, custom_outputs_json string, error string")
    .withColumn("_scored_at", F.current_timestamp())
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.scoring_response"))
display(spark.table(f"{FQ}.scoring_response"))
