# Omnigent に送るプロンプト（Step 2 エージェントをゼロから作る）

採点基準（どの観点を何点にするか）は業務の決めごとなので、できあがったもの（`02_agent/solution/rubric.py`）をそのまま使います。
エージェントの処理（LangGraph のグラフ・AI Search・Memory）を Omnigent に作ってもらいます。

プロンプトは 2 回に分けて送ります。1 回目でグラフの設計を確かめてから、2 回目で作ってもらうと、意図とずれにくくなります。

## 1 回目: 設計を確かめる

```
handson/README.md の「スコアリングエージェントの仕様」を満たすエージェントを、LangGraph で作りたいです。
採点基準は handson/02_agent/solution/rubric.py をそのまま使います（handson/my_work/rubric.py にコピーしてください）。
rubric.py にある関数（axis_prompt・adjustment_prompt・SUMMARY_PROMPT・axis_result_problem・
adjustment_result_problem・assemble_score_result）を読み、次の処理の流れでグラフを設計してください。
まだコードは書かず、ノードと辺の一覧、状態（State）の項目、各ノードの入出力を表で示してください。

処理の流れ:
1. prepare: AI Search で過去の受注事例を 1 回だけ検索する（検索語は企業特性の industry・summary・recent_trigger・
   key_facts から作る）。Managed Agent Memory から、共通ルール（scope "shared"）、観点別のルール（scope "rubric_<観点>"）、
   会社別の記憶（scope "<会社ID>"）を読む。
2. score_axis: 5 観点と関係性の補正の 6 つを、LangGraph の Send で同時に採点する。各観点には、その観点のプロンプト・
   企業特性・事例・その観点に関係する記憶だけを渡す（補正には企業特性と会社別の記憶だけ）。LLM の出力を
   axis_result_problem / adjustment_result_problem で確かめ、問題があれば理由を伝えて 1 回だけやり直させる。
3. 6 つがそろったら 1 回だけ分岐する: どれかが基準に合わなければ fail（点数を出さず axis_errors を返す）、合えば summarize。
4. summarize: 確定した点数を変えずに、SUMMARY_PROMPT でコメント・次のアクション・根拠を書かせる。
5. assemble: assemble_score_result で合計・Tier・確からしさを計算する（LLM に計算させない）。
6. save_history: custom_inputs.save_history が true のときだけ、採点の結果を会社別の記憶に書き込む。
```

## 2 回目: 作ってもらう

```
その設計で、次の 3 つのファイルを handson/my_work/ に作ってください。
memory.py と agent.py はエージェント本体なので、普通の Python ファイルにします（先頭に "# Databricks notebook source" を
付けない。Model Serving にもこのまま載せる）。02_try_agent.py はそれを読み込んで動かすノートブックにします。

1. memory.py（Managed Agent Memory の読み書き。Python ファイル）
   - Memory は Unity Catalog の Memory Store（名前は _config.py の MEMORY_STORE）。REST API を使う:
     一覧 GET /api/2.1/unity-catalog/memory-stores/<store>/entries?scope=<scope>（本文は返らない）、
     本文 GET /api/2.1/unity-catalog/memory-stores/<store>/entries:get?scope=<scope>&path=<path>、
     書き込み POST /api/2.1/unity-catalog/memory-stores/<store>/entries?scope=<scope>（body に path・contents・description）。
   - read(ws, store, scope) は、その scope の記憶を全部読んで本文をつなげて返す（なければ空文字）。
   - 認証: Model Serving の中（環境変数 IS_IN_DB_MODEL_SERVING_ENV が "true"）では、呼び出したユーザー本人の資格情報
     （OBO）を使う。トークンは mlflowserving.scoring_server.agent_utils の fetch_obo_token() でリクエストごとに取り、
     databricks-sdk の CredentialsStrategy を実装したクラスで、そのリクエスト専用の WorkspaceClient に固定する。
     取れなければ例外にする（ほかの資格情報に切り替えない）。それ以外の場所では WorkspaceClient() をそのまま使う。

2. agent.py（LangGraph のグラフと MLflow の ResponsesAgent。Python ファイル）
   - 設定は環境変数 HANDSON_CATALOG・HANDSON_SCHEMA・HANDSON_CASE_INDEX・HANDSON_LLM_ENDPOINT
     （既定 databricks-claude-sonnet-5）から読む。HANDSON_CASE_INDEX は、代表者が作った共有の AI Search のインデックス。
   - LLM は databricks_langchain の ChatDatabricks、AI Search は databricks_langchain の VectorSearchRetrieverTool
     （columns は case_id・title・content、num_results 3）。
   - LLM は今日の日付を知らないので、各観点の入力に「今日の日付」（日本時間）を入れる。
   - LLM の出力からは ```json フェンスの JSON を取り出す。推論ブロック付きの応答（content がリスト）にも対応する。
   - ResponsesAgent の predict: 会社IDは custom_inputs.company_id（なければ企業特性の company_id）。
     出力は本文（コメント＋```json フェンスの score_result）と custom_outputs.score_result。
     predict_stream は predict の結果を 1 回で返すだけでよい。
   - 先頭で mlflow.langchain.autolog() を呼び、最後に mlflow.models.set_model(AGENT) で登録する（model-from-code）。

3. 02_try_agent.py（動作確認のノートブック）
   - handson/02_agent/solution/02_try_agent.py と同じ流れで、エージェントのフォルダを ../my_work にする。
   - 環境変数 HANDSON_CATALOG・HANDSON_SCHEMA・HANDSON_CASE_INDEX・HANDSON_LLM_ENDPOINT を _config.py の値
     （CATALOG・SCHEMA・CASE_INDEX・LLM_ENDPOINT）で設定してから、agent.py を import する。
   - エクスペリメントは _config.py の EXPERIMENT_PATH に、トレースの保存先を Unity Catalog（自分のスキーマ、
     table_prefix "scoring"）にして作る。

ライブラリは handson/requirements.txt のバージョンに合わせてください。
できたら、ワークスペースの handson/my_work/ に反映してください。
```

## 動かしてみて、うまくいかないとき

Omnigent に、エラーの全文と一緒に次のように頼みます。

```
my_work/02_try_agent を実行したら、次のエラーになりました。原因を調べて直してください。
直したら、どこをなぜ直したかを 3 行で説明してください。
<エラーの全文>
```
