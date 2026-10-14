# Omnigent に送るプロンプト（Step 3 オフライン評価）

## 評価のノートブックを作る

```
handson/03_evaluation/README.md の「評価データ」と「スコアラー」のとおりに、MLflow でオフライン評価する
Databricks ノートブックを handson/my_work/03_evaluate.py として作ってください。

条件:
- 先頭で handson/requirements.txt のライブラリを %pip で入れ、%run ../_config を実行する。
- ノートブック（ソース形式）にする。エージェント本体（agent.py などの Python ファイル）は変えずに import して使う。
- エージェントは handson/my_work/ の agent.py を読み込んで、ノートブックの中で直接呼ぶ（デプロイはまだしない）。
  環境変数 HANDSON_CATALOG・HANDSON_SCHEMA・HANDSON_CASE_INDEX・HANDSON_LLM_ENDPOINT を _config.py の値で設定してから読み込む。
- エクスペリメントは _config.py の EXPERIMENT_PATH（Step 2 で作ったもの）を使う。
  トレースを読むため、環境変数 MLFLOW_TRACING_SQL_WAREHOUSE_ID に _config.py の WAREHOUSE_ID を入れる。
- handson/03_evaluation/eval_dataset.json を、mlflow.genai.datasets で Unity Catalog の評価データセット
  （_config.py の FQ の中の scoring_eval_dataset）として登録する。inputs は company_id と characteristics_json、
  expectations は JSON の expectations をそのまま使う。前の内容が混ざらないよう、すでにあれば消してから作り直す。
- スコアラーは README の表の 4 つ。コードのスコアラーは mlflow.genai.scorers の @scorer で書き、
  理由（rationale）には、実際の値と期待値を書く。
- meets_expected_points は MLflow 組み込みの ExpectationsGuidelines を使い、期待値の expected_points を guidelines として渡す。
  ジャッジには、出力を {"score_result": ...} の JSON の文字列にして渡す（dict のままだと中の項目を読めないことがある）。
- predict_fn は、評価データの inputs を受け取り、エージェントの predict を呼んで
  {"response": 本文, "score_result": custom_outputs.score_result} を返す。
- mlflow.genai.evaluate で評価し、スコアラーごとの平均を表示する。

できたら、ワークスペースの handson/my_work/ に反映してください。
```

## 直すとき（例）

原因がわかったら、直したい内容を具体的に伝えます。

```
評価で E00X が NG になりました。理由は「<Genie Code で調べてわかったこと>」です。
<直したい内容。例: 採点基準の〇〇を△△に変える>ように、handson/my_work/ のファイルを直してください。
採点基準を変えた場合は RUBRIC_VERSION を 1 つ上げてください。
直したらワークスペースに反映し、どのファイルのどこを変えたかを教えてください。
```
