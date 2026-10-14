# Step 1 自分のデータを用意し、共有の AI Search で事例を検索する（20 分）

## このステップでやること
1. Omnigent に、自分のデータを用意するノートブックを作ってもらい、実行する
2. Step 0 で代表者が作った **共有の AI Search（旧 Vector Search）インデックス** を Databricks の画面で開き、検索してみる

## 用意するデータ

| データ | 元のファイル | 作るもの | 置き場所 |
|---|---|---|---|
| 自社 CRM（3 社） | `data/crm_accounts.json` | `crm_account` テーブル | 自分のスキーマ |
| ディープリサーチの結果（3 社） | `data/research/<会社ID>/research.md` | Volume `research` の同じフォルダ構成 | 自分のスキーマ |
| 採点の共通ルール | — | Managed Agent Memory（`agent_memory`）の `shared` の記憶 | 自分のスキーマ |
| 過去の受注事例（10 件） | `data/reference_cases.json` | `reference_case` テーブル・`reference_case_index` インデックス | **共有スキーマ（代表者が Step 0 で作成済み）** |

## 演習

### 1-1. データを用意する（Omnigent）
[exercise/prompt_prepare_data.md](exercise/prompt_prepare_data.md) のプロンプトを Omnigent に送ります。
できたノートブック（`my_work/01_prepare_data`）を Databricks の画面で開き、**すべて実行** します。

確認すること:
- **カタログ** で自分のスキーマを開き、`crm_account` テーブルと `research` Volume があること
- `research` Volume の中に、`C001`・`C002`・`C003` のフォルダと `research.md` があること

### 1-2. 共有のインデックスを見る（Databricks の画面）
1. **カタログ** → 共有スキーマ `agent_handson_shared` → `reference_case_index` を開く
2. **概要** で、元のテーブル（`reference_case`）・主キー（`case_id`）・埋め込みの列（`content`）・埋め込みモデルを確かめる
3. 元のテーブル `reference_case` も開き、`content` 列にどんな文章が入っているかを見る

> **ポイント**: Delta Sync のインデックスは、元のテーブルの変更を **Change Data Feed** で取り込みます。
> 事例を足したら、インデックスの **今すぐ同期** を押すだけで検索対象に入ります。

### 1-3. 検索してみる（Databricks の画面）
インデックスの画面の **検索** に、次のような文を入れて結果を見ます。

- `病院 電子カルテ 人手不足` → RC03（総合病院グループ）が上に来る
- `EC 会員アプリ 不正ログイン` → RC08（大手小売の EC）が上に来る
- `銀行 勘定系 金融庁 証跡` → RC02（地方銀行の共同センター）が上に来る
- `クラウドのマネージドサービス中心で修正の対象が小さい SaaS 企業` → RC10（適合が低い例）が上に来る

> 短い語（例: `クラウドネイティブ 小規模`）だと、狙った事例が上に来ないことがあります。意味で検索するため、文で書くほうが当たりやすくなります。

エージェントは Step 2 で、企業特性の業種・要約・きっかけから検索語を作り、同じように事例を探します。

## うまくいかないとき
- 1-1: 模範解答 [solution/01_prepare_data](solution/01_prepare_data.py) をそのまま実行します。
- 1-2・1-3: 共有のインデックスが見つからない・検索できないときは、代表者に Step 0 の手順 5 が終わっているか、権限が付いているかを確かめてもらいます。
