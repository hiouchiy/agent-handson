# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2 エージェントを動かしてトレースを見る（模範解答）
# MAGIC 1. MLflow のエクスペリメントを作り、トレースを **Unity Catalog の Delta テーブル（自分のスキーマ）に同期** する
# MAGIC    （Step 4 のデプロイ後のトレースも、同じエクスペリメントに入り、同じテーブルに同期される）
# MAGIC 2. エージェントを読み込み、1 社を採点する
# MAGIC 3. エクスペリメントの「トレース」タブで、グラフの各ノード（AI Search の検索・観点ごとの採点）を確認する
# MAGIC 4. 同期されたトレースを SQL で見る（同期は 15 分ごとなので、テーブルに入るまで少しかかる）

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
from mlflow.tracing.archival import enable_databricks_trace_archival

# エージェントが読む設定（Model Serving では、デプロイ時に同じ値を環境変数で渡す）
os.environ.update({"HANDSON_CATALOG": CATALOG, "HANDSON_SCHEMA": SCHEMA, "HANDSON_CASE_INDEX": CASE_INDEX,
                   "HANDSON_LLM_ENDPOINT": LLM_ENDPOINT})
experiment = mlflow.set_experiment(EXPERIMENT_PATH)
print("エクスペリメント:", experiment.experiment_id)
# 以前の版の教材で、トレースの保存先を Unity Catalog にした同じ名前のエクスペリメントが残っていると、トレースを同期できない
if getattr(experiment, "trace_location", None):
    raise RuntimeError(f"エクスペリメント {EXPERIMENT_PATH} は、トレースの保存先が Unity Catalog になっています。"
                       "エクスペリメントの画面で名前を変えて（例: agent_handson_scoring_old）から、もう一度実行してください")

# エクスペリメントのトレースを、自分のスキーマの Delta テーブルに同期する（15 分ごとに、自分の権限で動くジョブが作られる）。
# デプロイしたエージェントは資格情報を持たずにエクスペリメントへトレースを送り、そこからこのテーブルに入る
try:
    enable_databricks_trace_archival(delta_table_fullname=TRACE_TABLE, experiment_id=experiment.experiment_id)
except Exception as e:  # 2 回目以降の実行では、すでに同期が有効になっている
    if "409" not in str(e) and "already" not in str(e).lower():
        raise
    print("同期はすでに有効です:", TRACE_TABLE)

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
# MAGIC
# MAGIC ## 同期されたトレースを SQL で見る
# MAGIC トレースは 15 分ごとに `scoring_traces` テーブルに同期されます。テーブルがまだない・空のときは、Step 3 のあとでこのセルをもう一度実行します。
# MAGIC 1 トレースが 1 行で、各処理（スパン）は `spans`、フィードバックや評価は `assessments` に配列で入っています。

# COMMAND ----------

display(spark.sql(f"""
  SELECT trace_id, request_time, execution_duration_ms / 1000 AS seconds, s.name AS span,
         (unix_millis(s.end_time) - unix_millis(s.start_time)) / 1000 AS span_seconds
  FROM {TRACE_TABLE} LATERAL VIEW explode(spans) AS s
  ORDER BY request_time DESC, span_seconds DESC LIMIT 20"""))
