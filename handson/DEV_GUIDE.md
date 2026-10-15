# 開発の決まり（コーディングエージェント向け）

このハンズオンで、Omnigent がコードを書くときに必ず従う決まりです。
参加者は業務の言葉で要件を書きます。**要件を技術に置き換えるのは Omnigent の仕事** で、そのときにこのファイルの対応表と決まりを使います。

> 実際の組織では、このようなファイルを社内の基盤チームが一度用意しておくと、業務の人は要件を書くだけでエージェントを作れるようになります。

## 要件の言葉と、使う技術の対応

| 要件でこう書かれていたら | 使う技術 | 参考 |
|---|---|---|
| AI エージェントを作る | LangGraph の `StateGraph` で処理の流れを組み、MLflow の `ResponsesAgent` で包む（Model Serving の入出力） | `02_agent/solution/agent.py` |
| AI（LLM）に判断させる・文章を書かせる | `databricks_langchain.ChatDatabricks`（エンドポイントは環境変数 `HANDSON_LLM_ENDPOINT`） | |
| 観点ごとに同時に採点する | LangGraph の `Send` で 6 つ（5 観点＋関係性の補正）に分け、そろったら次へ進む | |
| 採点基準（rubric.md）に従う | `rubric.py` の関数でプロンプトを作り、出力を確かめる（採点基準の中身を `agent.py` に書き写さない） | `rubric.py` |
| 段階と点数が合わなければやり直させる | `rubric.axis_result_problem`・`adjustment_result_problem` で見つけ、理由を添えて 1 回だけ聞き直す | |
| 合計・Tier は計算で出す | `rubric.assemble_score_result`（LLM に計算させない） | |
| 過去の受注事例から似ているものを探す | `databricks_langchain.VectorSearchRetrieverTool`（インデックスは環境変数 `HANDSON_CASE_INDEX`）。1 回の採点で 1 回だけ検索する | |
| 共通ルール・会社ごとの申し送りを覚えておいて使う／結果を覚えておく | Managed Agent Memory。`memory.py` の `read`・`write` を使う。scope は共通ルール `shared`、観点別のルール `rubric_<観点>`、会社別 `<会社ID>`。結果は `custom_inputs.save_history` が true のときだけ書く | `memory.py` |
| 呼び出した人の権限で記憶を読む | Model Serving では `memory.client_for_request()`（呼び出したユーザーの代理＝OBO）。リクエストごとに取り、取れなければエラーにする | `memory.py` |
| 今日の日付で判断する | `memory.today()`（日本時間）を各観点の入力に入れる | |
| 会社の特徴が入っていない質問には使い方を返す | エラーにせず、エージェントの説明と入力の例を返す（`score_result` は None） | |
| 期待どおりに動いているかを評価する | `mlflow.genai.evaluate`。形のチェックはコードのスコアラー、文章の中身は `ExpectationsGuidelines`（出力は JSON の文字列にして渡す） | `03_evaluation/solution/03_evaluate.py` |
| 文章から決まった形の情報を取り出す（ジョブのタスク） | `ai_query` に `responseFormat`（JSON Schema・strict）を付ける。`failOnError` は付けない（戻り値のフィールド名がスキルやドキュメントの説明と違うことがある）。出力は `try_parse_json` で確かめ、読めない行は別のテーブルに分ける | `05_job_dashboard/solution/task1_extract_characteristics.py` |
| 処理の記録を残して見る | MLflow のトレース。エクスペリメントに集め、Delta テーブル（`TRACE_TABLE`）に同期する | `02_agent/solution/02_try_agent.py` |
| API として公開する・人の感想を集める | `databricks.agents.deploy`（Model Serving と Review App）。資格情報（個人用アクセストークンなど）は渡さない | `04_deploy_review_app/solution/04_deploy.py` |

## エージェント本体（agent.py）の決まり
- 置き場所は `handson/my_work/agent.py`。普通の Python ファイルにする（先頭に `# Databricks notebook source` を付けない）
- 同じフォルダの `rubric.py` と `memory.py` を `import` して使う（`solution/` からコピーしたもの）
- 設定は環境変数 `HANDSON_CATALOG`・`HANDSON_SCHEMA`・`HANDSON_CASE_INDEX`・`HANDSON_LLM_ENDPOINT` から読む
- 最後に `AGENT = <ResponsesAgent のインスタンス>` と `mlflow.models.set_model(AGENT)` を書く（用意したノートブックがこの名前で読み込む）
- 入出力は `handson/README.md` の「スコアリングエージェントの仕様」のとおりにする
- 動作確認は、用意してあるノートブック `02_agent/solution/02_try_agent` を、ウィジェット `agent_dir=../../my_work` で実行する

## どの Step でも守ること
- ライブラリは `handson/requirements.txt` のバージョンに合わせる。使う関数・引数・戻り値の形が、そのバージョンにあることを確かめる（推測で書かない）
- 用意してあるノートブック（各 Step の `solution/`）は、使うように言われたら書き直さない
- 要件にない処理（結果を読み直して確かめる処理など）を足さない
- 書いたら `python3 -m py_compile` で構文を確かめる。None や空になりうる戻り値は、確かめてから使う
- 分からないことは、Databricks のスキル（databricks-core など）と、上の表の「参考」のファイルで調べる
