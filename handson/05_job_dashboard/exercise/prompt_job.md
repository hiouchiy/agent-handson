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
- ノートブックは書き直さない。ここでは実行もしない（5-2 でジョブとして実行する）
```
