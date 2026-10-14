# Omnigent に送るプロンプト（Step 4 デプロイ）

**このプロンプトで頼んでいること**: Step 3 で直したエージェントを、Model Serving にデプロイするノートブックを作ってもらう。

```
## やりたいこと
my_work のエージェントを、Model Serving にデプロイするノートブックを作ってください。

## 作るもの
- ファイル: handson/my_work/04_deploy.py（ノートブック）
- 中身:
  1. エージェントを MLflow に記録する（model-from-code。agent.py が本体、rubric.py と memory.py も一緒に入れる）
  2. Unity Catalog に登録する
  3. databricks.agents.deploy で Model Serving にデプロイし、エンドポイント名と Review App の URL を表示する
  4. エンドポイントの準備ができるまで待つ
  5. 評価データの 1 件目をエンドポイントに送り、score・tier・next_action を表示する

## 決まりごと
- エージェント本体（agent.py・rubric.py・memory.py）は変えない
- 名前（モデル・エンドポイント・エクスペリメントなど）は %run ../_config で読み込んだ変数を使う。
  エクスペリメントは Step 2 のもの（デプロイ後のトレースも同じ場所に入れる）
- 依存は handson/requirements.txt と同じバージョンに固定する（databricks-agents は除く）
- 使うリソース（LLM・埋め込みモデル・AI Search のインデックス）は、システムの認証で宣言する。
  Memory は呼び出したユーザーとして読むので、ユーザーの認証（スコープ unity-catalog）も付ける

## 気をつけること
- デプロイ後のトレースを Unity Catalog のテーブルに書くには、自分の個人用アクセストークン（有効期限 3 日）を Secret に入れ、
  デプロイの環境変数で DATABRICKS_TOKEN（Secret の参照）・DATABRICKS_AUTH_TYPE=pat・DATABRICKS_HOST を渡す
  （エンドポイント自身の ID にはトレースのテーブルの権限がない。AUTH_TYPE を pat にしないとトークンが使われない）
- 記録するときに agent.py を読み込むので、my_work を sys.path に入れておく
- agents.deploy は古いバージョンを流量 0% で残すので、準備ができたら今回のバージョン以外を外す

## 参考にするもの
- 同じことをするノートブック: handson/04_deploy_review_app/solution/04_deploy.py
- デプロイの書き方: Databricks のスキル（databricks-model-serving）

## できたら
ワークスペースに反映して、実行してよいか聞いてください（デプロイの完了まで 20〜25 分かかります）。
完了の条件: エンドポイントから採点結果が返ってきて、Review App の URL が表示されること。
```
