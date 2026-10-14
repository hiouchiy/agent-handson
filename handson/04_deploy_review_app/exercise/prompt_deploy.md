# Omnigent に送るプロンプト（Step 4 デプロイ）

```
handson/my_work/ のエージェント（agent.py・rubric.py・memory.py）を Model Serving にデプロイする
Databricks ノートブックを handson/my_work/04_deploy.py として作ってください。

条件:
- ノートブック（ソース形式）にする。エージェント本体（agent.py・rubric.py・memory.py の Python ファイル）は変えない。
- 先頭で handson/requirements.txt のライブラリを %pip で入れ、%run ../_config を実行する。
- エクスペリメントは _config.py の EXPERIMENT_PATH を使う（デプロイ後のトレースも同じ場所に入れるため）。
- mlflow.pyfunc.log_model で model-from-code として記録する。python_model は agent.py、
  code_paths に rubric.py と memory.py を入れる。記録するときに agent.py が import できるよう、
  my_work を sys.path に入れておく。
- 依存は handson/requirements.txt と同じバージョンに固定する（databricks-agents は除く）。
- input_example には、企業特性の JSON と custom_inputs.company_id を入れる。
- auth_policy:
  - SystemAuthPolicy の resources に、LLM（_config.py の LLM_ENDPOINT）・埋め込みモデル（EMBEDDING_ENDPOINT）・
    AI Search のインデックス（CASE_INDEX）を宣言する。
  - UserAuthPolicy(api_scopes=["unity-catalog"]) を付ける（Managed Agent Memory を呼び出したユーザーとして読むため）。
- デプロイ後のトレースを Unity Catalog のテーブル（scoring_otel_*）に書けるよう、自分の個人用アクセストークン
  （有効期限 3 日）を databricks-sdk で作り、Secret スコープ agent_handson_<PARTICIPANT> のキー tracing_token に入れる
  （スコープがなければ作る）。エンドポイント自身の ID には、トレースのテーブルへの権限がないため。
- Unity Catalog の MODEL_NAME に登録し、databricks.agents.deploy で ENDPOINT_NAME にデプロイする。
  environment_vars に HANDSON_CATALOG・HANDSON_SCHEMA・HANDSON_CASE_INDEX・HANDSON_LLM_ENDPOINT と、
  DATABRICKS_TOKEN（値は "{{secrets/<スコープ>/tracing_token}}"）、DATABRICKS_AUTH_TYPE（"pat"）、
  DATABRICKS_HOST（ワークスペースの URL）を渡す。AUTH_TYPE を pat にしないと、Serving の中ではエンドポイント自身の
  資格情報が優先されてトレースが書けない。scale_to_zero は true。
- デプロイ後に、エンドポイント名と Review App の URL を表示する。
- エンドポイントの準備ができたら、今回のバージョン以外（agents.deploy が流量 0% で残す古いバージョン）をエンドポイントから外す。
- 最後のセルで、評価データの 1 件目をエンドポイントに送り、score・tier・next_action を表示する。

できたら、ワークスペースの handson/my_work/ に反映してください。
```
