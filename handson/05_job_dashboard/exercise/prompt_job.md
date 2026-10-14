# Omnigent に送るプロンプト（Step 5 ジョブのタスク）

**このプロンプトで頼んでいること**: 定期実行するジョブの 3 つのタスク（企業特性を作る・エージェントを呼ぶ・結果を書く）を、ノートブックで作ってもらう。

```
## やりたいこと
handson/05_job_dashboard/README.md の「作るジョブ」の 3 つのタスクを、ノートブックで作ってください。
ジョブとして実行するので、ここでは作るだけにします。

## 作るもの
| ファイル | やること | 出力 |
|---|---|---|
| handson/my_work/task1_extract_characteristics.py | Volume の会社ごとの research.md を読み、自社 CRM と合わせて、ai_query で企業特性の JSON にする | company_characteristic |
| handson/my_work/task2_score.py | 1 社ずつ、スコアリングエージェントのエンドポイントを呼ぶ（save_history を true にする） | scoring_response |
| handson/my_work/task3_write_results.py | 応答から採点結果を取り出し、観点ごとの点数を列にして書く。失敗した行は別のテーブルへ | customer_product_score・customer_product_score_rejected |

## 決まりごと
- 名前（テーブル・Volume・エンドポイント・モデル）は %run ../_config で読み込んだ変数を使う
- 企業特性の項目は、handson/README.md の「スコアリングエージェントの仕様」のとおりにする
- task1 では判断をさせず、事実の整理だけにする
- 1 社の失敗でタスク全体を止めない（エラーの内容を記録して次の会社へ）

## 気をつけること
- task1: research.md は 1 ファイル 1 行で読み、会社IDはファイルのパス（_metadata.file_path）から取り出す。
  ai_query の出力の形は、responseFormat に JSON Schema（strict）で指定する（指定しないと JSON が崩れることがある）
- task2: エンドポイントは databricks-sdk の api_client で /serving-endpoints/<名前>/invocations を呼び、会社IDは custom_inputs で渡す

## 参考にするもの
- 同じことをするノートブック: handson/05_job_dashboard/solution/ の task1〜3
- ai_query の書き方: Databricks のスキル（databricks-ai-functions）

## できたら
ワークスペースに反映して、作ったノートブックとそれぞれの出力のテーブルを表にして教えてください（実行はしない）。
```
