# Omnigent に送るプロンプト（Step 5 ジョブのタスク）

**このプロンプトで頼んでいること**: 定期実行するジョブの 3 つのタスク（企業特性を作る・エージェントを呼ぶ・結果を書く）について、用意してあるノートブックの中身を説明してもらう。
タスクのノートブックは用意したもの（`solution/` の task1〜3）を使い、5-2 で Omnigent にジョブとして組み立ててもらいます。

```
## やりたいこと
Step 5 のジョブのタスクは、用意してあるノートブックを、書き直さずにそのまま使います。
- handson/05_job_dashboard/solution/task1_extract_characteristics.py
- handson/05_job_dashboard/solution/task2_score.py
- handson/05_job_dashboard/solution/task3_write_results.py

それぞれが何を読み、何をして、どのテーブルに書くかを、表にして説明してください。
特に、task1 の ai_query（responseFormat で出力の形を決めているところ）と、task3 で失敗した行を別のテーブルに分けるところを説明してください。

## 決まりごと
<<<<<<< HEAD
- ノートブックは書き直さない。ここでは実行もしない（5-2 でジョブとして実行する）
=======
- 名前（テーブル・Volume・エンドポイント・モデル）は %run ../_config で読み込んだ変数を使う
- 企業特性の項目は、handson/README.md の「スコアリングエージェントの仕様」のとおりにする
- task1 では判断をさせず、事実の整理だけにする
- 1 社の失敗でタスク全体を止めない（エラーの内容を記録して次の会社へ）

## 気をつけること
- task1: research.md は 1 ファイル 1 行で読み、会社IDはファイルのパス（_metadata.file_path）から取り出す。
  ai_query の出力の形は、responseFormat に JSON Schema（strict）で指定する（指定しないと JSON が崩れることがある）
- task1: ai_query に failOnError を付けない（付けたときの戻り値のフィールド名が、スキルやドキュメントの説明と違うことがある）。
  出力は try_parse_json で確かめ、JSON として読めない行は別のテーブルに分ける（模範解答と同じ）
- タスクのノートブックは、模範解答（handson/05_job_dashboard/solution/ の task1〜3）と同じ書き方・同じ関数にする
- task2: エンドポイントは databricks-sdk の api_client で /serving-endpoints/<名前>/invocations を呼び、会社IDは custom_inputs で渡す

## 参考にするもの
- 同じことをするノートブック: handson/05_job_dashboard/solution/ の task1〜3
- ai_query の書き方: Databricks のスキル（databricks-ai-functions）

## できたら
ワークスペースに反映して、作ったノートブックとそれぞれの出力のテーブルを表にして教えてください（実行はしない）。
>>>>>>> main
```
