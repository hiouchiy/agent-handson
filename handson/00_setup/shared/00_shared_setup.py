# Databricks notebook source
# MAGIC %md
# MAGIC # Step 0 共有の準備（代表者 1 名だけが実行する）
# MAGIC 参加者全員で使う、過去の受注事例の **AI Search（旧 Vector Search）** を用意します。
# MAGIC
# MAGIC | 作るもの | 名前 | 全員に付ける権限 |
# MAGIC |---|---|---|
# MAGIC | 共有スキーマ | `<カタログ>.agent_handson_shared` | `USE SCHEMA`・`SELECT`（`account users`） |
# MAGIC | 過去の受注事例のテーブル | `reference_case`（Change Data Feed を有効にする） | スキーマの `SELECT` で読める |
# MAGIC | AI Search のエンドポイント | `_config.py` の `AI_SEARCH_ENDPOINT` | `CAN_USE`（ワークスペースの `users`） |
# MAGIC | AI Search のインデックス | `reference_case_index`（Delta Sync、埋め込みは `databricks-gte-large-en`） | スキーマの `SELECT` で検索できる |
# MAGIC
# MAGIC 最後のセルで、ほかの参加者が使えるかを確かめる検索をします。全部で 10〜15 分かかります（ほとんどがインデックスの準備の待ち時間）。

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import json
import os
import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    EndpointType,
    PipelineType,
    VectorIndexType,
)

w = WorkspaceClient()
DATA_DIR = os.path.abspath("../../data")
ALL_USERS_UC = "account users"  # Unity Catalog の権限は、アカウントのグループに付ける
ALL_USERS_WS = "users"          # ワークスペースのオブジェクト（エンドポイント）の権限は、ワークスペースのグループに付ける

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 共有スキーマと過去の受注事例のテーブル

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SHARED_FQ} COMMENT 'スコアリングのハンズオンで全員が使う共有データ'")
cases = json.load(open(f"{DATA_DIR}/reference_cases.json", encoding="utf-8"))
spark.createDataFrame(cases).select("case_id", "industry", "title", "content") \
    .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(CASE_TABLE)
spark.sql(f"ALTER TABLE {CASE_TABLE} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
display(spark.table(CASE_TABLE))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. AI Search のエンドポイント（なければ作る）

# COMMAND ----------

try:
    endpoint = w.vector_search_endpoints.get_endpoint(AI_SEARCH_ENDPOINT)
    print("エンドポイントはすでにあります:", AI_SEARCH_ENDPOINT)
except NotFound:
    endpoint = w.vector_search_endpoints.create_endpoint_and_wait(name=AI_SEARCH_ENDPOINT,
                                                                  endpoint_type=EndpointType.STANDARD)
    print("エンドポイントを作成しました:", AI_SEARCH_ENDPOINT)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. AI Search のインデックス（なければ作る。あれば同期する）

# COMMAND ----------

try:
    w.vector_search_indexes.get_index(CASE_INDEX)
    w.vector_search_indexes.sync_index(CASE_INDEX)
    print("インデックスはすでにあります。同期を始めました:", CASE_INDEX)
except NotFound:
    w.vector_search_indexes.create_index(
        name=CASE_INDEX, endpoint_name=AI_SEARCH_ENDPOINT, primary_key="case_id",
        index_type=VectorIndexType.DELTA_SYNC,
        delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
            source_table=CASE_TABLE, pipeline_type=PipelineType.TRIGGERED,
            embedding_source_columns=[EmbeddingSourceColumn(name="content",
                                                            embedding_model_endpoint_name=EMBEDDING_ENDPOINT)]))
    print("インデックスを作成しました:", CASE_INDEX)

# 最初の同期が終わるまで待つ（作成直後のエンドポイントでは 10 分ほどかかる）。
# 状態の ready はインデックスができた時点で true になるので、取り込んだ行数が元のテーブルと同じになるまで待つ
expected = spark.table(CASE_TABLE).count()
start = time.time()
while True:
    status = w.vector_search_indexes.get_index(CASE_INDEX).status
    if status.ready and (status.indexed_row_count or 0) >= expected:
        break
    print(f"{int(time.time() - start)} 秒: 取り込み {status.indexed_row_count or 0}/{expected} 件 - {status.message}")
    time.sleep(30)
print(f"インデックスの同期が終わりました（{status.indexed_row_count} 件）")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 参加者全員に権限を付ける

# COMMAND ----------

# Unity Catalog: カタログを使い、共有スキーマの中を読める（テーブルを読む・インデックスを検索する）
spark.sql(f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `{ALL_USERS_UC}`")
spark.sql(f"GRANT USE SCHEMA, SELECT ON SCHEMA {SHARED_FQ} TO `{ALL_USERS_UC}`")

# AI Search のエンドポイント: 全員が使える
w.api_client.do("PATCH", f"/api/2.0/permissions/vector-search-endpoints/{endpoint.id}", body={
    "access_control_list": [{"group_name": ALL_USERS_WS, "permission_level": "CAN_USE"}]})

display(spark.sql(f"SHOW GRANTS ON SCHEMA {SHARED_FQ}"))
acl = w.api_client.do("GET", f"/api/2.0/permissions/vector-search-endpoints/{endpoint.id}")
print([(a.get("group_name") or a.get("user_name"), [p["permission_level"] for p in a["all_permissions"]])
       for a in acl["access_control_list"]])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. 検索してみる

# COMMAND ----------

from databricks.sdk.errors import BadRequest


def search(query, tries=10):
    """同期の直後は「not ready」になることがあるので、少し待ってやり直す。"""
    for _ in range(tries):
        try:
            return w.vector_search_indexes.query_index(index_name=CASE_INDEX, columns=["case_id", "title"],
                                                       query_text=query, num_results=3)
        except BadRequest as e:
            if "not ready" not in str(e):
                raise
            time.sleep(30)
    raise TimeoutError("インデックスの準備が終わりません")


for query in ["病院 電子カルテ 人手不足", "EC 会員アプリ 不正ログイン"]:
    print(query, "→", [row[0] for row in search(query).result.data_array])
