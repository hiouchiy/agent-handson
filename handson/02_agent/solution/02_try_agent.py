# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2 エージェントを動かしてトレースを見る（模範解答）
# MAGIC 1. MLflow のエクスペリメントを作る。トレースの保存先を **Unity Catalog（自分のスキーマ）** にする
# MAGIC    （OpenTelemetry 形式で Delta テーブルに保存される。Step 4 のデプロイ後のトレースも同じ場所に入る）
# MAGIC 2. エージェントを読み込み、1 社を採点する
# MAGIC 3. エクスペリメントの「トレース」タブで、グラフの各ノード（AI Search の検索・観点ごとの採点）を確認する

# COMMAND ----------

# MAGIC %pip install -q -r ../../requirements.txt
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import os
import sys

dbutils.widgets.text("agent_dir", "../../02_agent/solution", "エージェントのコードがあるフォルダ")
AGENT_DIR = os.path.abspath(dbutils.widgets.get("agent_dir"))

import mlflow
from mlflow.entities.trace_location import UnityCatalog

# エージェントが読む設定（Model Serving では、デプロイ時に同じ値を環境変数で渡す）
os.environ.update({"HANDSON_CATALOG": CATALOG, "HANDSON_SCHEMA": SCHEMA, "HANDSON_CASE_INDEX": CASE_INDEX,
                   "HANDSON_LLM_ENDPOINT": LLM_ENDPOINT})
# Unity Catalog に保存したトレースを読むときに使う SQL ウェアハウス
os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = WAREHOUSE_ID

# トレースの保存先は、エクスペリメントを作るときにだけ指定できる（あとから変えられない）
experiment = mlflow.set_experiment(
    experiment_name=EXPERIMENT_PATH,
    trace_location=UnityCatalog(catalog_name=CATALOG, schema_name=SCHEMA, table_prefix="scoring"))
print("エクスペリメント:", experiment.experiment_id, experiment.trace_location)

sys.path.insert(0, AGENT_DIR)
from agent import AGENT  # noqa: E402

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 社を採点する
# MAGIC 入力は「企業特性」の JSON（Step 5 のジョブでは、ディープリサーチの結果から作る）。会社IDは `custom_inputs` で渡す。

# COMMAND ----------

import json

characteristics = {
    "company_id": "T001", "company_name": "北陸ガスネットワーク株式会社", "industry": "ガス",
    "is_critical_infra": True, "regulated": True, "legacy_scale": "高", "security_staffing": "逼迫",
    "size_class": "大", "public_exposure": "中",
    "recent_trigger": "2026年4月、供給管理システムの未修正の脆弱性を外部から指摘され、緊急点検を実施",
    "existing_relationship": "取引なし（新規）",
    "key_facts": ["従業員 約8,200人", "供給管理の制御系を長期運用", "セキュリティ担当は数名で兼務が多い"],
    "summary": "重要インフラ×古い制御系×直近の外部指摘。",
}
request = {
    "input": [{"role": "user", "content": "次の企業特性をスコアリングしてください。\n"
                                          + json.dumps(characteristics, ensure_ascii=False)}],
    "custom_inputs": {"company_id": "T001"},
}
response = AGENT.predict(request)
score_result = response.custom_outputs["score_result"]
print(json.dumps(score_result, ensure_ascii=False, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## トレースを確認する
# MAGIC 上のセルの出力に表示されるトレースを開くか、左のメニュー **エクスペリメント** → `agent_handson_scoring` → **トレース** を開きます。
# MAGIC - `prepare` の中の **retriever** のスパン: AI Search で見つかった事例
# MAGIC - `score_axis` が 6 回並んで動いている: 5 観点と関係性の補正
# MAGIC
# MAGIC 保存先の Delta テーブルは SQL でも見られます。

# COMMAND ----------

display(spark.sql(f"""
  SELECT trace_id, name, time,
         (end_time_unix_nano - start_time_unix_nano) / 1e9 AS seconds
  FROM {FQ}.scoring_otel_spans
  ORDER BY time DESC LIMIT 20"""))
