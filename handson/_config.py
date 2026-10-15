# Databricks notebook source
# MAGIC %md
# MAGIC # ハンズオン共通の設定
# MAGIC 各ノートブックの先頭で `%run ../_config`（または `%run ../../_config`）として読み込みます。
# MAGIC 値はすべて `handson/settings.json` から読みます。このノートブックは書き換えません。
# MAGIC - `instructor`: 全員共通の値（講師が教材を配る前に入れる）
# MAGIC - `participant`: 参加者ごとの値（参加者が Step 0 で入れる）

# COMMAND ----------

import json
import os
import re


def _find_settings(start: str) -> str:
    """呼び出したノートブックのフォルダから上にさかのぼって settings.json を探す。"""
    d = os.path.abspath(start)
    while True:
        for candidate in (os.path.join(d, "settings.json"), os.path.join(d, "handson", "settings.json")):
            if os.path.exists(candidate):
                return candidate
        parent = os.path.dirname(d)
        if parent == d:
            raise FileNotFoundError("handson/settings.json が見つかりません")
        d = parent


SETTINGS_PATH = _find_settings(os.getcwd())
SETTINGS = json.load(open(SETTINGS_PATH, encoding="utf-8"))
_inst, _part = SETTINGS["instructor"], SETTINGS["participant"]
_missing = [k for k in ("catalog", "warehouse_id") if not _inst.get(k)]
if _missing:
    raise ValueError(f"settings.json の instructor に値が入っていません: {_missing}（講師が教材を配る前に入れます）")

CATALOG = _inst["catalog"]
AI_SEARCH_ENDPOINT = _inst["ai_search_endpoint"]
LLM_ENDPOINT = _inst["llm_endpoint"]                  # スコアリングに使う基盤モデル
EXTRACT_LLM_ENDPOINT = _inst["extract_llm_endpoint"]  # ジョブで企業特性を抜き出す基盤モデル（ai_query）
EMBEDDING_ENDPOINT = _inst["embedding_endpoint"]
WAREHOUSE_ID = _inst["warehouse_id"]                  # ダッシュボードなどに使う SQL ウェアハウス

# 全員で共有するスキーマ（事前準備で、過去の受注事例のテーブルと AI Search のインデックスを作っておく）
SHARED_SCHEMA = _inst["shared_schema"]
SHARED_FQ = f"{CATALOG}.{SHARED_SCHEMA}"
CASE_TABLE = f"{SHARED_FQ}.reference_case"
CASE_INDEX = f"{SHARED_FQ}.reference_case_index"

# 参加者ごとのスキーマ（メールアドレスの @ より前から作る。例: taro.yamada → agent_handson_taro_yamada）
USER_NAME = spark.sql("SELECT current_user()").first()[0]
if _part.get("user_email") and _part["user_email"].lower() != USER_NAME.lower():
    print(f"注意: settings.json の user_email（{_part['user_email']}）と、実行しているユーザー（{USER_NAME}）が違います。"
          "このノートブックは実行しているユーザーの名前で進めます。")
PARTICIPANT = re.sub(r"[^a-z0-9]+", "_", USER_NAME.split("@")[0].lower()).strip("_")
SCHEMA = f"agent_handson_{PARTICIPANT}"

# 参加者ごとのリソース名
FQ = f"{CATALOG}.{SCHEMA}"
CRM_TABLE = f"{FQ}.crm_account"
MEMORY_STORE = f"{FQ}.agent_memory"  # Managed Agent Memory（Unity Catalog の MEMORY_STORE）
RESEARCH_VOLUME = f"/Volumes/{CATALOG}/{SCHEMA}/research"
MODEL_NAME = f"{FQ}.scoring_agent"
ENDPOINT_NAME = f"scoring-agent-{PARTICIPANT.replace('_', '-')}"[:63]
EXPERIMENT_PATH = f"/Users/{USER_NAME}/agent_handson_scoring"
TRACE_TABLE = f"{FQ}.scoring_traces"  # エクスペリメントのトレースを同期する Delta テーブル

print(f"設定ファイル: {SETTINGS_PATH}\n参加者: {USER_NAME}\nスキーマ: {FQ}\n共有のインデックス: {CASE_INDEX}\n"
      f"Memory: {MEMORY_STORE}\nエンドポイント: {ENDPOINT_NAME}\nエクスペリメント: {EXPERIMENT_PATH}\nトレースのテーブル: {TRACE_TABLE}")
