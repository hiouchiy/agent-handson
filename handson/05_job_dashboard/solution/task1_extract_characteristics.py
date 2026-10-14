# Databricks notebook source
# MAGIC %md
# MAGIC # ジョブ タスク 1: ディープリサーチの結果から企業特性を作る（模範解答）
# MAGIC - 入力: Volume `research/<会社ID>/research.md`（前段の公開情報取得ジョブの出力）と、自社 CRM（`crm_account`）
# MAGIC - 処理: `ai_query` で、スコアリングエージェントの入力形式（企業特性の JSON）に整理する
# MAGIC - 出力: `company_characteristic` テーブル（1 社 1 行）。JSON として読めなかった行は入れない

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import json

from pyspark.sql import functions as F

# 会社ごとのフォルダにある research.md を、1 ファイル 1 行で読む（パスから会社IDを取り出す）
docs = (spark.read.format("text").option("wholetext", "true").option("recursiveFileLookup", "true")
        .option("pathGlobFilter", "research.md").load(RESEARCH_VOLUME)
        .select(F.regexp_extract(F.col("_metadata.file_path"), r"/research/([^/]+)/research\.md$", 1).alias("company_id"),
                F.col("value").alias("research_text")))
docs.createOrReplaceTempView("docs")
spark.table(CRM_TABLE).createOrReplaceTempView("crm")
display(docs.select("company_id", F.length("research_text").alias("chars")))

# COMMAND ----------

PROMPT = """あなたは法人向けセキュリティサービスの見込み顧客を判定するために、
企業の公開情報を整理する分析担当です。判断（何点か・売れそうか）はしません。事実の整理だけをします。
次の公開情報と自社 CRM から、指定の JSON だけを出力してください。わからない項目は "不明" にします。
- legacy_scale: 古いシステム・大規模なシステムの多さ（高/中/低）
- security_staffing: セキュリティ人材の状況（逼迫/一部逼迫/十分）
- size_class: 企業規模（大/中/小）
- public_exposure: インターネットに公開している資産の多さ（高/中/低）
- recent_trigger: 直近のインシデント・監査での指摘・規制強化・システム刷新など。時期も書く。なければ "なし"
- existing_relationship: 自社 CRM の内容の要約（既存取引・競合製品・商談の状況）
- key_facts: 根拠になる事実を 3〜6 個（従業員数・売上などの数値があれば含める）
- summary: 見込みの観点での一言"""

# 出力の形を JSON Schema で決める（スコアリングエージェントの入力の仕様と同じ項目）
_str = {"type": "string"}
RESPONSE_FORMAT = json.dumps({"type": "json_schema", "json_schema": {"name": "characteristics", "strict": True, "schema": {
    "type": "object", "additionalProperties": False,
    "required": ["company_id", "company_name", "industry", "is_critical_infra", "regulated", "legacy_scale",
                 "security_staffing", "size_class", "public_exposure", "recent_trigger", "existing_relationship",
                 "key_facts", "summary"],
    "properties": {
        "company_id": _str, "company_name": _str, "industry": _str,
        "is_critical_infra": {"type": "boolean"}, "regulated": {"type": "boolean"},
        "legacy_scale": {"type": "string", "enum": ["高", "中", "低", "不明"]},
        "security_staffing": {"type": "string", "enum": ["逼迫", "一部逼迫", "十分", "不明"]},
        "size_class": {"type": "string", "enum": ["大", "中", "小", "不明"]},
        "public_exposure": {"type": "string", "enum": ["高", "中", "低", "不明"]},
        "recent_trigger": _str, "existing_relationship": _str,
        "key_facts": {"type": "array", "items": _str}, "summary": _str}}}}, ensure_ascii=False)

result = spark.sql(f"""
  SELECT d.company_id, c.company_name,
         ai_query('{EXTRACT_LLM_ENDPOINT}',
                  concat(:prompt, '\\n\\ncompany_id は ', d.company_id, ' と書く。',
                         '\\n\\n# 自社 CRM\\n', to_json(named_struct(
                             'existing_customer', c.existing_customer, 'current_products', c.current_products,
                             'open_opportunity', c.open_opportunity, 'incumbent_security_vendor', c.incumbent_security_vendor)),
                         '\\n\\n# 公開情報\\n', d.research_text),
                  responseFormat => :response_format) AS characteristics_json
  FROM docs d LEFT JOIN crm c USING (company_id)""", args={"prompt": PROMPT, "response_format": RESPONSE_FORMAT})

(result.filter("try_parse_json(characteristics_json) IS NOT NULL")
    .withColumn("_extracted_at", F.current_timestamp())
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FQ}.company_characteristic"))
display(spark.table(f"{FQ}.company_characteristic"))
