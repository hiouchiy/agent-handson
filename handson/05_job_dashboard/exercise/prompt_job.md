# Omnigent に送るプロンプト（Step 5 ジョブのタスク）

```
handson/05_job_dashboard/README.md の「作るジョブ」の 3 つのタスクを、Databricks ノートブックとして
handson/my_work/ に作ってください（task1_extract_characteristics.py・task2_score.py・task3_write_results.py）。
どれも先頭で %run ../_config を実行し、_config.py の変数を使ってください。

task1_extract_characteristics:
- RESEARCH_VOLUME の下の <会社ID>/research.md を、1 ファイル 1 行で読む（spark.read.format("text") の
  wholetext・recursiveFileLookup・pathGlobFilter）。会社IDはファイルのパス（_metadata.file_path）から取り出す。
- CRM_TABLE と会社IDで結合する。
- ai_query（モデルは EXTRACT_LLM_ENDPOINT）で、README の「スコアリングエージェントの仕様」の企業特性の項目を持つ
  JSON にする。出力の形は responseFormat に JSON Schema（strict）で指定する。判断はさせず、事実の整理だけにする。
- JSON として読めない行は除き、company_characteristic テーブルに上書きで保存する。

task2_score:
- company_characteristic を読み、1 社ずつ ENDPOINT_NAME のエンドポイントを呼ぶ
  （POST /serving-endpoints/<名前>/invocations を databricks-sdk の api_client で呼ぶ。並列は 4）。
- リクエストは {"input":[{"role":"user","content":"次の企業特性をスコアリングしてください。\n" + 企業特性}],
  "custom_inputs":{"company_id": 会社ID, "save_history": true}}。
- 応答の custom_outputs を JSON の文字列のまま scoring_response テーブルに保存する。1 社の失敗で止めず、
  エラーの内容を error 列に入れる。

task3_write_results:
- scoring_response の custom_outputs から score_result を取り出し、score・tier・5 観点の点数（列に展開）・
  relationship_adjustment・confidence・next_action・rationale・key_signals・matched_cases・axis_details（JSON）・
  rubric_version を列にして、customer_product_score に上書きで保存する。業種は company_characteristic から入れる。
- 呼び出しに失敗した行・点数が出なかった行（axis_errors がある）は customer_product_score_rejected に理由と一緒に入れる。

できたら、ワークスペースの handson/my_work/ に反映してください。
```
