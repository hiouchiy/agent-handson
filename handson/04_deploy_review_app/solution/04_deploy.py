# Databricks notebook source
# MAGIC %md
# MAGIC # Step 4 Model Serving にデプロイし、Review App で人のフィードバックを集める（模範解答）
# MAGIC 1. エージェントを MLflow に記録する（model-from-code）→ Unity Catalog に登録する
# MAGIC 2. `databricks.agents.deploy` で Model Serving にデプロイする（Review App も一緒にできる）
# MAGIC 3. エンドポイントを呼んでみる。トレースは Step 2 と同じエクスペリメントに入り、同じ Delta テーブルに同期される
# MAGIC 4. Review App で採点結果を見て、👍／👎 とコメントを付ける
# MAGIC
# MAGIC **認証の考え方**
# MAGIC | 使うもの | 認証 |
# MAGIC |---|---|
# MAGIC | 基盤モデル・埋め込みモデル・AI Search のインデックス | エンドポイントの資格情報（デプロイ時に「使うリソース」として宣言する） |
# MAGIC | Managed Agent Memory | 呼び出したユーザー本人の資格情報（OBO）。Memory は「使うリソース」として宣言できないため |
# MAGIC | トレース | エンドポイントの資格情報でエクスペリメントに送る。Delta テーブルへの同期は、Step 2 で有効にした自分のジョブが行う |
# MAGIC
# MAGIC どれも、個人用アクセストークンなどの資格情報をエンドポイントに渡す必要はありません。

# COMMAND ----------

# MAGIC %pip install -q -r ../../requirements.txt
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import os
import sys

import mlflow
from mlflow.models.auth_policy import AuthPolicy, SystemAuthPolicy, UserAuthPolicy
from mlflow.models.resources import DatabricksServingEndpoint, DatabricksVectorSearchIndex

dbutils.widgets.text("agent_dir", "../../03_evaluation/solution/fixed", "エージェントのコードがあるフォルダ")
AGENT_DIR = os.path.abspath(dbutils.widgets.get("agent_dir"))
sys.path.insert(0, AGENT_DIR)  # 記録するときに agent.py を読み込むので、同じフォルダの rubric.py・memory.py を見つけられるようにする

AGENT_ENV = {"HANDSON_CATALOG": CATALOG, "HANDSON_SCHEMA": SCHEMA, "HANDSON_CASE_INDEX": CASE_INDEX, "HANDSON_LLM_ENDPOINT": LLM_ENDPOINT}
os.environ.update(AGENT_ENV)
mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(EXPERIMENT_PATH)  # デプロイ後のトレースも、このエクスペリメントに入る

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 記録して登録する

# COMMAND ----------

auth_policy = AuthPolicy(
    system_auth_policy=SystemAuthPolicy(resources=[
        DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT),
        DatabricksServingEndpoint(endpoint_name=EMBEDDING_ENDPOINT),
        DatabricksVectorSearchIndex(index_name=CASE_INDEX),
    ]),
    user_auth_policy=UserAuthPolicy(api_scopes=["unity-catalog"]),  # Memory を呼び出したユーザーとして読み書きする
)

# MLflow は記録するときに、この入力例でエージェントを 1 回動かして確かめる
input_example = {
    "input": [{"role": "user", "content": "次の企業特性をスコアリングしてください。\n"
               '{"company_id":"T001","industry":"ガス","is_critical_infra":true,"regulated":true,'
               '"legacy_scale":"高","security_staffing":"逼迫","size_class":"大","public_exposure":"中",'
               '"recent_trigger":"2026年4月、供給管理システムの脆弱性を外部から指摘された",'
               '"existing_relationship":"取引なし（新規）"}'}],
    "custom_inputs": {"company_id": "T001"},
}

with open("../../requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("databricks-agents")]

with mlflow.start_run(run_name="log_scoring_agent"):
    info = mlflow.pyfunc.log_model(
        name="agent",
        python_model=f"{AGENT_DIR}/agent.py",
        code_paths=[f"{AGENT_DIR}/rubric.py", f"{AGENT_DIR}/memory.py"],
        input_example=input_example,
        auth_policy=auth_policy,
        pip_requirements=requirements,
    )
version = mlflow.register_model(info.model_uri, MODEL_NAME).version
print("登録しました:", MODEL_NAME, "バージョン", version)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. デプロイする（15〜20 分ほどかかります）
# MAGIC 待っている間に、エンドポイントの画面（**サービング** → 自分のエンドポイント）でデプロイの進み具合を見られます。

# COMMAND ----------

from databricks import agents
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
deployment = agents.deploy(MODEL_NAME, int(version), endpoint_name=ENDPOINT_NAME, scale_to_zero=True,
                           environment_vars=AGENT_ENV)
print("エンドポイント:", deployment.endpoint_name)
print("Review App:", deployment.review_app_url)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. エンドポイントを呼ぶ
# MAGIC エンドポイントの準備ができるまで待ってから実行します（状態が「準備完了」になっていること）。

# COMMAND ----------

import json
from datetime import timedelta

from mlflow.deployments import get_deploy_client

# 準備ができるまで待つ（デプロイの直後は 15〜20 分かかる）
endpoint = w.serving_endpoints.wait_get_serving_endpoint_not_updating(
    ENDPOINT_NAME, timeout=timedelta(minutes=40))
print("エンドポイントの状態:", endpoint.state.ready, endpoint.state.config_update)

# 古いバージョンをエンドポイントから外す。agents.deploy は古いバージョンを流量 0% のまま残すので、
# デプロイをやり直すたびに積み重なり、そのどれかが使うもの（インデックスなど）を消すと次のデプロイが失敗する
path = f"/api/2.0/serving-endpoints/{ENDPOINT_NAME}"
entities = w.api_client.do("GET", path)["config"]["served_entities"]
if any(str(e["entity_version"]) != str(version) for e in entities):
    keep = next(e for e in entities if str(e["entity_version"]) == str(version))
    keep = {k: v for k, v in keep.items() if k not in ("state", "creation_timestamp", "creator") and v is not None}
    w.api_client.do("PUT", f"{path}/config", body={
        "served_entities": [keep],
        "traffic_config": {"routes": [{"served_model_name": keep["name"], "traffic_percentage": 100}]}})
    endpoint = w.serving_endpoints.wait_get_serving_endpoint_not_updating(ENDPOINT_NAME, timeout=timedelta(minutes=40))
    print("古いバージョンを外しました。残っているバージョン:", [e.entity_version for e in endpoint.config.served_entities])

characteristics = json.load(open("../../03_evaluation/eval_dataset.json", encoding="utf-8"))[0]
response = get_deploy_client("databricks").predict(endpoint=ENDPOINT_NAME, inputs={
    "input": [{"role": "user", "content": "次の企業特性をスコアリングしてください。\n"
               + characteristics["characteristics_json"]}],
    "custom_inputs": {"company_id": characteristics["company_id"]}})
sr = response["custom_outputs"]["score_result"]
print(sr["company_id"], sr["score"], sr["tier"], sr["next_action"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Review App で人のフィードバックを付ける
# MAGIC 1. 上で表示した Review App の URL を開く（チャット画面）
# MAGIC 2. 入力欄に、評価データの企業特性を貼り付けて送る
# MAGIC    （Review App から呼ぶときは会社IDを `custom_inputs` で渡せないので、エージェントは本文の `company_id` を使う）
# MAGIC 3. 回答に 👍／👎 を付け、理由をコメントに書く（例: 「次のアクションに競合の契約時期が入っていない」）
# MAGIC 4. エクスペリメント → **トレース** で、付けたフィードバックが評価（assessment）としてトレースに残っていることを確認する
# MAGIC 5. 15 分ほど待ってから次のセルを実行し、デプロイ後のトレースとフィードバックが Delta テーブルにも同期されたことを確かめる

# COMMAND ----------

display(spark.sql(f"""
  SELECT trace_id, request_time, state, request_preview,
         transform(assessments, a -> concat(a.name, ': ', coalesce(a.feedback.value, a.expectation.value))) AS assessments
  FROM {TRACE_TABLE}
  ORDER BY request_time DESC LIMIT 10"""))
