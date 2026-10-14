# Step 5 ジョブで定期実行し、結果をダッシュボードで見る（30 分）

## 前提
前段の「公開情報取得ジョブ」（ディープリサーチ）が、会社ごとのフォルダに調べた結果を書き出しているとします。

```
/Volumes/<カタログ>/<スキーマ>/research/
├── C001/research.md   株式会社ホクト住まいホールディングス
├── C002/research.md   ミライネクストグループ株式会社
└── C003/research.md   株式会社ツナグマーケット
```

## 作るジョブ

| タスク | やること | 出力 |
|---|---|---|
| `extract_characteristics` | フォルダを 1 つずつ読み、自社 CRM と合わせて、`ai_query` で企業特性の JSON にする | `company_characteristic` |
| `score` | 1 社ずつスコアリングエージェントのエンドポイントを呼ぶ（`save_history=true`） | `scoring_response` |
| `write_results` | 応答を整形し、観点ごとの点数を列にして Delta テーブルに書く。失敗した行は別のテーブルへ | `customer_product_score`・`customer_product_score_rejected` |

- エージェントは採点の結果を、会社別の **長期記憶（Managed Agent Memory）** に書き込みます（`save_history=true` のときだけ）。
  次の日の採点では、前回の点数や次のアクションを踏まえて採点します。
- 評価（Step 3）では書き込みません。書き込むと、次の評価で前回の結果を参照してしまい、評価の結果が変わるためです。

## 演習

### 5-1. ジョブのタスクを作る（Omnigent）
[exercise/prompt_job.md](exercise/prompt_job.md) のプロンプトを Omnigent に送り、3 つのタスクのノートブックを作ってもらいます。
Omnigent が「このまま実行しますか？」と聞いてきたら、「5-2 でジョブとして実行するので、今は実行しない」と答えます。

### 5-2. ジョブを作って動かす
ジョブの中身は次のとおりです（計算資源はサーバーレス、種類はノートブック）。

| タスク名 | ノートブック | 依存するタスク |
|---|---|---|
| `extract_characteristics` | `my_work/task1_extract_characteristics` | — |
| `score` | `my_work/task2_score` | `extract_characteristics` |
| `write_results` | `my_work/task3_write_results` | `score` |

スケジュールは毎朝 6 時（日本時間）で、**一時停止** にしておきます。作り方は 2 通りあります。

**A（おすすめ）: Omnigent に作ってもらう**

```
handson/05_job_dashboard/README.md の 5-2 の表のとおりに、3 つのタスクのジョブを Databricks CLI で作ってください
（ノートブックはワークスペースの my_work の下のもの。計算資源はサーバーレス、スケジュールは毎朝 6 時・日本時間で一時停止）。
作ったら、ジョブを 1 回実行し、終わるまで待って、各タスクの結果とジョブの画面の URL を教えてください。
失敗したタスクがあれば、原因を調べて直し、もう一度実行してください。
```

**B: Databricks の画面で作る**
1. **ジョブとパイプライン** → **作成** → **ジョブ**
2. 上の表の 3 つのタスクを追加する
3. **スケジュール** で毎朝 6 時（日本時間）を設定し、**一時停止** にしておく
4. **今すぐ実行** を押し、3 つのタスクが成功することを確かめる（3〜5 分）

**どちらの場合も、終わったら Databricks の画面で確かめます**
1. ジョブの画面で、3 つのタスクの実行の流れ（グラフ）と、各タスクの出力を見る
2. **カタログ** で `customer_product_score` を開き、3 社の点数と Tier が入っていることを確かめる
3. Memory に採点の履歴が入ったことを確かめる（Genie Code に「自分の Memory の scope C001 の記憶を表示して」と頼むなど）

### 5-3. ダッシュボードを作る（Databricks の画面）
1. **ダッシュボード** → **作成** → **ダッシュボード**
2. **データ** タブで `customer_product_score` を追加する
3. 次のウィジェットを置く（Genie Code に「このデータで、見込み顧客のダッシュボードを作って」と頼んでもよい）
   - 採点した会社の数・優良見込み（Tier A・B）の数・平均スコア
   - 会社ごとの、観点別の点数（積み上げの横棒グラフ）
   - 会社・スコア・Tier・次のアクション・参考にした事例・根拠の表
4. **公開** する

## うまくいかないとき
- タスク: [solution/](solution/) の `task1_extract_characteristics`・`task2_score`・`task3_write_results`
- ジョブ: [solution/05_create_job](solution/05_create_job.py) を実行すると、同じジョブを作って実行します
- ダッシュボード: [solution/scoring.lvdash.json](solution/scoring.lvdash.json) を **ダッシュボード** → **作成** の横の **インポート** から読み込みます
  （読み込んだ後、データのカタログとスキーマを自分のものにします）
