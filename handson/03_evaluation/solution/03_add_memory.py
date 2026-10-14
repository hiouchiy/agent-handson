# Databricks notebook source
# MAGIC %md
# MAGIC # Step 3 改善: 会社別の申し送りを Memory に足す（模範解答）
# MAGIC E001（東和電力ネットワーク）は、CRM 上は「競合の脆弱性管理サービスを導入済み」なので、関係性の補正が大きくマイナスになります。
# MAGIC 一方で営業担当は、訪問で「競合との契約は 2026 年 12 月末で満了し、更新しない方針」と聞いています。
# MAGIC この申し送りは CRM には入っていないので、**エージェントの長期記憶（Managed Agent Memory）** に入れておきます。
# MAGIC 採点基準には「契約更新が 6 か月以内なら 1 段階軽くする」とあるので、次の採点から補正が変わります。

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
API = "/api/2.1/unity-catalog/memory-stores"
w.api_client.do("POST", f"{API}/{MEMORY_STORE}/entries", query={"scope": "E001"}, body={
    "path": "/memories/episodic/contract.md",
    "contents": ("東和電力ネットワークは競合 A 社の脆弱性管理サービス（MSS）を導入しているが、契約は 2026 年 12 月末で満了する。"
                 "先方の情報システム部長から、更新はせず乗り換えを検討する方針と聞いている（2026 年 9 月の訪問）。"
                 "更新前の 2026 年 11 月までに提案したい。"),
    "description": "営業担当からの申し送り"})

for e in w.api_client.do("GET", f"{API}/{MEMORY_STORE}/entries", query={"scope": "E001"}).get("entries", []):
    print(e["scope"], e["path"], "-", e.get("description"))
