# Databricks notebook source
# MAGIC %md
# MAGIC # Step 1-1 データの準備（模範解答）
# MAGIC 次のものを自分のスキーマに作ります。
# MAGIC
# MAGIC | 作るもの | 中身 | 使う場所 |
# MAGIC |---|---|---|
# MAGIC | `crm_account` テーブル | 自社 CRM（3 社分） | Step 5 のジョブで企業特性に入れる |
# MAGIC | `research` Volume | ディープリサーチの結果（3 社分、会社ごとのフォルダ） | Step 5 のジョブの入力 |
# MAGIC | `agent_memory`（Managed Agent Memory） | 採点の共通ルール | エージェントが毎回読む |
# MAGIC
# MAGIC 過去の受注事例のテーブルと AI Search のインデックスは、Step 0 で代表者が共有スキーマに作ったものを使います。

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import json
import os
import shutil

DATA_DIR = os.path.abspath("../../data")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FQ}")
print(DATA_DIR)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 自社 CRM

# COMMAND ----------

crm = json.load(open(f"{DATA_DIR}/crm_accounts.json", encoding="utf-8"))
spark.createDataFrame(crm).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(CRM_TABLE)
display(spark.table(CRM_TABLE))

# COMMAND ----------

# MAGIC %md
# MAGIC ## ディープリサーチの結果を Volume に置く
# MAGIC 前段の「公開情報取得ジョブ」が、会社ごとのフォルダに `research.md` を書き出した状態を再現します。

# COMMAND ----------

spark.sql(f"CREATE VOLUME IF NOT EXISTS {FQ}.research")
for company_id in sorted(os.listdir(f"{DATA_DIR}/research")):
    os.makedirs(f"{RESEARCH_VOLUME}/{company_id}", exist_ok=True)
    shutil.copy(f"{DATA_DIR}/research/{company_id}/research.md", f"{RESEARCH_VOLUME}/{company_id}/research.md")
display(dbutils.fs.ls(RESEARCH_VOLUME))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Managed Agent Memory を作り、共通ルールを入れる
# MAGIC Memory は Unity Catalog のオブジェクト（`MEMORY_STORE`）として、自分のスキーマに作ります。
# MAGIC エントリは **scope**（誰／何についての記憶か）と **path**（名前）で管理します。
# MAGIC - `shared`: 全社で共通のルール（全観点で読む）
# MAGIC - `rubric_<観点>`: その観点だけを補足するルール（今は空）
# MAGIC - `<会社ID>`: 会社ごとの申し送りや、過去の採点の履歴（エージェントが書き込む）

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
API = "/api/2.1/unity-catalog/memory-stores"
try:
    w.api_client.do("GET", f"{API}/{MEMORY_STORE}")
    print("Memory はすでにあります:", MEMORY_STORE)
except Exception:
    w.api_client.do("POST", API, body={"name": "agent_memory", "catalog_name": CATALOG, "schema_name": SCHEMA,
                                       "description": "スコアリングエージェントの長期記憶"})
    print("Memory を作成しました:", MEMORY_STORE)

SCORING_RULES = """# スコアリングの共通ルール
- 理想的な顧客: 重要インフラ（電力・通信・鉄道・ガス・水道・空港・交通）、古いシステムや大規模なシステムが多い、
  セキュリティ人材が足りない、規制業種（金融・医療・公共）、直近のインシデント・監査での指摘がある。
- 適合が低い顧客: クラウドネイティブで自社で修正を当てる対象が小さい、競合がすでに入っていて提案の余地がない。
- 直近の当局への報告・情報漏えい・監査での指摘は、最優先で訪問すべききっかけ。"""

existing = w.api_client.do("GET", f"{API}/{MEMORY_STORE}/entries", query={"scope": "shared"}).get("entries", [])
if not existing:
    w.api_client.do("POST", f"{API}/{MEMORY_STORE}/entries", query={"scope": "shared"},
                    body={"path": "/memories/semantic/scoring_rules.md", "contents": SCORING_RULES,
                          "description": "スコアリングの共通ルール"})
for e in w.api_client.do("GET", f"{API}/{MEMORY_STORE}/entries", query={"scope": "shared"}).get("entries", []):
    print(e["scope"], e["path"], "-", e.get("description"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 共有のインデックスを検索できることを確かめる
# MAGIC 過去の受注事例のインデックスは、Step 0 で代表者が共有スキーマに作ったものです。

# COMMAND ----------

res = w.vector_search_indexes.query_index(index_name=CASE_INDEX, columns=["case_id", "title"],
                                          query_text="病院 電子カルテ 人手不足", num_results=3)
for row in res.result.data_array:
    print(row)
