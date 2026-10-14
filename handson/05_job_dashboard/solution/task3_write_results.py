# Databricks notebook source
# MAGIC %md
# MAGIC # ジョブ タスク 3: 採点の結果を Delta テーブルに書く（模範解答）
# MAGIC - 入力: `scoring_response`（タスク 2 の出力）と `company_characteristic`
# MAGIC - 出力: `customer_product_score`（ダッシュボードが読む。1 社 1 行、観点ごとの点数は列に展開）
# MAGIC   と `customer_product_score_rejected`（呼び出しの失敗・採点が基準に合わなかった行）

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

from pyspark.sql import functions as F

AXES = ["need_vuln", "critical_regulated", "staffing_gap", "size_budget", "timing"]
sr_schema = f"""struct<company_id:string, company_name:string, score:int, tier:string,
  subscores:struct<{', '.join(f'{a}:int' for a in AXES)}>, relationship_adjustment:int,
  key_signals:array<string>, matched_cases:array<string>, next_action:string, confidence:string,
  rationale:string, rubric_version:string, axis_errors:map<string,string>>"""

resp = (spark.table(f"{FQ}.scoring_response")
        .withColumn("sr", F.from_json(F.get_json_object("custom_outputs_json", "$.score_result"), sr_schema))
        .withColumn("axis_details_json", F.get_json_object("custom_outputs_json", "$.score_result.axis_details")))

ok = resp.filter("error IS NULL AND sr.score IS NOT NULL AND sr.axis_errors IS NULL")
chars = spark.table(f"{FQ}.company_characteristic").select(
    "company_id", F.get_json_object("characteristics_json", "$.industry").alias("industry"))

(ok.join(chars, "company_id", "left")
    .select("company_id", F.col("sr.company_name").alias("company_name"), "industry",
            F.col("sr.score").alias("score"), F.col("sr.tier").alias("tier"),
            *[F.col(f"sr.subscores.{a}").alias(a) for a in AXES],
            F.col("sr.relationship_adjustment").alias("relationship_adjustment"),
            F.col("sr.confidence").alias("confidence"), F.col("sr.next_action").alias("next_action"),
            F.col("sr.rationale").alias("rationale"),
            F.concat_ws(" / ", "sr.key_signals").alias("key_signals"),
            F.concat_ws(", ", "sr.matched_cases").alias("matched_cases"),
            "axis_details_json", F.col("sr.rubric_version").alias("rubric_version"), "_scored_at")
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.customer_product_score"))

(resp.join(ok.select("company_id"), "company_id", "left_anti")
    .select("company_id", F.coalesce("error", F.to_json("sr.axis_errors"), F.lit("output_unparseable")).alias("reason"),
            "_scored_at")
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.customer_product_score_rejected"))

display(spark.table(f"{FQ}.customer_product_score").orderBy(F.desc("score")))
