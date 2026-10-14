# 講師の事前準備

当日までに、ハンズオンに使うワークスペースで次を済ませておきます。

## 1. ワークスペースで有効にしておく機能（管理者）

| 機能 | 使う Step | 確認方法 |
|---|---|---|
| Omnigent（ワークスペースのプレビュー） | 全体 | `<ワークスペースの URL>/omnigent` が開けること |
| Databricks Sandbox（ワークスペースのプレビュー） | 全体（Omnigent の実行場所） | Omnigent の New session で **Sandbox** を選べること |
| Managed Agent Memory（Unity Catalog の Memory Store） | 1〜5 | Step 1 の模範解答で Memory を作成できること |
| MLflow のトレースを Unity Catalog に保存する機能 | 2〜5 | Step 2 の模範解答で `scoring_otel_spans` テーブルができること |
| Model Serving のユーザー代理（On-Behalf-Of）認証 | 4〜5 | Step 4 の模範解答のデプロイが成功すること |
| Genie Code（Databricks Assistant のエージェントモード） | 3 | ノートブックで Assistant のエージェントモードを使えること |
| Omnigent の中から GitHub と PyPI・Databricks のスキル配布元（GitHub）に出られること | 0 | Step 0 の手順 4 で `databricks aitools install` が成功すること |

> **リージョンに注意**: Omnigent の実行場所（Sandbox）は、対応しているリージョンが限られています。
> ハンズオンのワークスペースのリージョンが対応しているか、事前に確認してください。

## 2. 共有のリソースを作る

| リソース | 作り方 | `_config.py` の設定 |
|---|---|---|
| カタログ | 参加者全員が `USE CATALOG`・`CREATE SCHEMA` できるカタログを用意する | `CATALOG` |
| AI Search のエンドポイント・インデックス | 当日、Step 0 で**代表者 1 名**が作る（プロンプト、またはノートブック `00_setup/shared/00_shared_setup`）。共有スキーマ `agent_handson_shared` に作り、全員に読み取り・検索の権限を付ける。作成直後のエンドポイントはインデックスがオンラインになるまで 10 分ほどかかるので、時間に余裕がなければ**前日までに講師がノートブックで作っておく** | `AI_SEARCH_ENDPOINT`（名前だけ決めておく） |
| SQL ウェアハウス | サーバーレスの SQL ウェアハウス。参加者に `CAN USE` を付ける | `WAREHOUSE_ID` |

### `handson/settings.json` に値を入れる
環境や参加者によって変わる値は `handson/settings.json` だけにあります（ノートブックの `_config.py` とすべてのプロンプトがここを読む）。
教材を配る前に、`instructor` の値を当日の環境に合わせて入れます。`participant` は空のままにします（参加者が Step 0 で入れる）。
**リポジトリの `settings.json` は空のままにしておき、配る ZIP の中のものだけに値を入れます**（当日の環境の情報をリポジトリに残さないため。手順は下の「教材の配り方」）。

| 項目 | 入れる値 |
|---|---|
| `workspace_url` | ハンズオンのワークスペースの URL |
| `catalog` | 全員が使うカタログ（下の「カタログ」） |
| `warehouse_id` | 全員が使う SQL ウェアハウスの ID |
| `shared_schema`・`ai_search_endpoint` | 既定のままでよい（`agent_handson_shared`・`agent-handson-ai-search`） |
| `llm_endpoint`・`extract_llm_endpoint`・`embedding_endpoint` | 既定のままでよい（ワークスペースにあることを確かめる） |

### カタログ
参加者全員が使えるカタログを 1 つ用意します（ハンズオン用に新しく作っても、既存の自由に使えるカタログでもよい）。
- 全員（`account users`）に `USE CATALOG` と `CREATE SCHEMA` を付ける
- このカタログの中に、共有スキーマ（Step 0 で代表者が作る）と、参加者全員の個人のスキーマ（各自の Step 0 で作る）ができる

### 教材の配り方（どちらかを選ぶ）
参加者は Step 0 の手順 2 で、次のどちらかで教材を受け取ります。どちらの場合も、Omnigent が作業場所に教材を置き、`settings.json` を埋めて、ワークスペースに取り込みます。

| | 基本: ZIP から | 別の方法: GitHub から |
|---|---|---|
| 講師の準備 | 下の手順で ZIP を作り（`settings.json` の `instructor` を埋める）、参加者に配る | 参加者の GitHub アカウントに、教材のリポジトリ（非公開）の読み取り権限を付ける。`instructor` に入れる値を参加者に案内する |
| 参加者がすること | Omnigent のチャットに ZIP を添付して、展開と取り込みを頼む | Omnigent に、クローンと `instructor` の値の書き込みと取り込みを頼む |

> お客様に配るときは **ZIP から** にします。GitHub から渡すと、リポジトリの持ち主などが見えてしまいます。

**ZIP の準備**（ZIP を作って参加者に配る。2・3 は、参加者が ZIP をチャットに添付できないときの予備）
1. GitHub の教材のリポジトリで **Code** → **Download ZIP** を押し、`agent-handson-main.zip` を手に入れる。
   展開して、`handson/instructor/`（評価データの種明かし）を消し、`handson/settings.json` の `instructor` に当日の値を入れてから、同じ名前で ZIP にし直す
   ```bash
   unzip agent-handson-main.zip && rm -rf agent-handson-main/handson/instructor
   # agent-handson-main/handson/settings.json の instructor に当日の値を入れる（エディタで編集）
   rm agent-handson-main.zip && zip -r agent-handson-main.zip agent-handson-main
   ```
2. Databricks で次を実行する（SQL エディタかノートブック）
   ```sql
   CREATE SCHEMA IF NOT EXISTS <カタログ>.agent_handson_shared;
   CREATE VOLUME IF NOT EXISTS <カタログ>.agent_handson_shared.materials;
   GRANT USE CATALOG ON CATALOG <カタログ> TO `account users`;
   GRANT USE SCHEMA, READ VOLUME ON SCHEMA <カタログ>.agent_handson_shared TO `account users`;
   ```
3. **カタログ** → `agent_handson_shared` → `materials` を開き、**この Volume にアップロード** で ZIP を置く

## 3. 参加者に必要な権限
- 教材: ZIP の場合は、予備として置く共有の Volume `materials` の `READ VOLUME`（上の「教材の配り方」）。GitHub の場合は、教材のリポジトリの読み取り
- カタログ: `USE CATALOG`、`CREATE SCHEMA`（自分のスキーマを作り、その中に表・Volume・Memory・モデルを作る）
- 共有スキーマ `agent_handson_shared`: `USE SCHEMA`・`SELECT`（代表者が Step 0 で `account users` に付ける）
- 代表者だけ: AI Search のエンドポイントを作れること、カタログと共有スキーマに権限を付けられること（カタログの所有者か `MANAGE` を持つ人）
- 基盤モデルのエンドポイント（`databricks-claude-sonnet-5`、`databricks-gpt-5-4-mini`、`databricks-gte-large-en`）: `CAN QUERY`
- AI Search のエンドポイント: `CAN_USE`（代表者が Step 0 でワークスペースの `users` に付ける）
- Model Serving のエンドポイントを作成できること
- 個人用アクセストークンを作れること、Secret スコープを作れること（Step 4 で、デプロイ後のトレースを書くために使う）
- ジョブを作成できること

## 4. 事前の通し確認
講師のユーザーで、各 Step の `solution/` を順に実行します。

1. `00_setup/00_check_config`
2. `00_setup/shared/00_shared_setup`（代表者の作業。AI Search のエンドポイント・インデックスと権限）
3. `01_data_ai_search/solution/01_prepare_data`
4. `02_agent/solution/02_try_agent`
5. `03_evaluation/solution/03_evaluate`（3 件とも NG になること）→ `03_add_memory` → `03_evaluate` をウィジェット `agent_dir=../../03_evaluation/solution/fixed` で実行（全件 OK になること）
6. `04_deploy_review_app/solution/04_deploy`
7. `05_job_dashboard/solution/05_create_job` → ダッシュボードを作成

## 5. 当日の注意
- Omnigent の権限のモードは **Accept edits（編集を承認）** にしてもらいます（auto にしない）。auto では、リソースを作るコマンドが理由なく拒否され、広い許可ルールも効きません。Step 0 の手順 1-2 で、ハンズオンで使うコマンドの許可ルール（`00_setup/claude_settings.json`）を入れてもらいます。
  - 事前に講師のユーザーで、1-2 のあとに `/permissions` で許可ルールが反映されること（組織の管理設定で、ユーザーの許可ルールが無視される設定になっていないこと）を確かめておきます。
- Omnigent は、ハンズオンの最後まで 1 つのセッションで作業してもらいます。新しいセッションを開くと別の Sandbox になり、入れたエージェントスキル・教材・作ったコードが引き継がれません。最初に参加者に伝えておきます。
- デプロイ（Step 4）は 15〜20 分かかります。待ち時間に Review App とトレースの説明を入れます。
- 評価データの NG は、わざと仕込んでいます。種明かしは [eval_answers.md](eval_answers.md) を参照してください（参加者には配りません）。

## 6. 配布するときの注意
- 参加者に配るリポジトリには `instructor/` フォルダを含めない（評価データの種明かしがあるため）。
- `03_evaluation/solution/` には直し方の模範解答が入っている。先に見られたくない場合は、Step 3 の開始後に配る。
