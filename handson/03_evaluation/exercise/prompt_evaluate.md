# Omnigent に送るプロンプト（Step 3 オフライン評価）

## 評価のノートブックを作る

**このプロンプトで頼んでいること**: 評価データを登録し、4 つのスコアラーでエージェントを評価するノートブックを作ってもらう。

```
## やりたいこと
MLflow で、エージェントのオフライン評価をするノートブックを作ってください。

## 作るもの
- ファイル: handson/my_work/03_evaluate.py（ノートブック）
- 中身:
  1. handson/03_evaluation/eval_dataset.json を、Unity Catalog の評価データセット scoring_eval_dataset として登録する
  2. README の「スコアラー」の 4 つのスコアラーを用意する
  3. my_work の agent.py を直接呼んで評価する（デプロイはまだしない）
  4. スコアラーごとの結果を表示する

## 決まりごと
- エージェント本体（agent.py などの Python ファイル）は変えずに import して使う
- 名前（スキーマ・エクスペリメントなど）は %run ../_config で読み込んだ変数を使う。エクスペリメントは Step 2 のものを使う
- 評価データセットは、前の内容が混ざらないよう、すでにあれば消してから作り直す
- スコアラーの理由（rationale）には、実際の値と期待値を書く

## 気をつけること
- meets_expected_points は MLflow 組み込みの ExpectationsGuidelines を使い、期待値の expected_points を guidelines として渡す。
  ジャッジには、出力を {"score_result": ...} の JSON の文字列にして渡す（dict のままだと中の項目を読めないことがある）
- トレースを読むため、環境変数 MLFLOW_TRACING_SQL_WAREHOUSE_ID に _config.py の WAREHOUSE_ID を入れる

## 参考にするもの
- 評価データとスコアラー: handson/03_evaluation/README.md の「評価データ」「スコアラー」
- MLflow の評価の書き方: Databricks のスキル（databricks-mlflow-evaluation）

## できたら
ワークスペースに反映して、実行してよいか聞いてください。
完了の条件: 評価が最後まで動き、評価データごとに、どのスコアラーが OK／NG かが表示されること（最初は NG が出ます）。
```

## 直すとき（例）

**このプロンプトで頼んでいること**: NG の原因が分かったあとで、直したい内容を伝えて直してもらい、もう一度評価してもらう。

```
## やりたいこと
評価で E00X が NG になったので、直してもう一度評価してください。

## NG の理由
<Genie Code で調べてわかったこと>

## 直したいこと
<例: 採点基準の〇〇を△△に変える>

## 決まりごと
- 採点基準（rubric.py）を変えた場合は RUBRIC_VERSION を 1 つ上げる

## できたら
どのファイルのどこを変えたかを教えてから、ワークスペースに反映して、評価をもう一度実行してよいか聞いてください。
```
