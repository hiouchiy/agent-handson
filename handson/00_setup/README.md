# Step 0 準備（15 分）

## このステップでやること

| # | やること | 誰が |
|---|---|---|
| 1 | Omnigent を起動し、権限のモードを「編集を承認」にする | 全員 |
| 2 | 教材を受け取る（Omnigent の作業場所と、Databricks のワークスペースの両方に置く）。最初の確認で、以降の Bash を確認なしにする | 全員 |
| 3 | Databricks のエージェントスキルを入れて、リロードする | 全員 |
| 4 | 作業のルールを Omnigent に伝える | 全員 |
| 5 | 設定ファイルに、カタログと SQL ウェアハウスを入れる（SQL ウェアハウスは Omnigent が調べて入れる） | 全員 |
| 6 | 全員で使う AI Search（エンドポイントとインデックス）を作る | **代表者 1 名だけ** |

教材を最初に受け取るので、手順 3 以降は、ワークスペースに取り込んだこの README を開いて、プロンプトをコピーしながら進められます。
代表者が 6 をやっている間に、ほかの参加者は 5 までを済ませます。

## 1. Omnigent を起動し、権限のモードを「編集を承認」にする
1. ブラウザで、講師から案内されたワークスペースの URL の後ろに `/omnigent` を付けたページを開く
2. **New session** → 実行場所に **Sandbox** を選ぶ
3. 権限のモードを **Accept edits（編集を承認）** にする。チャットの設定、または入力欄で `Shift+Tab` を押して切り替えます。
   **auto にはしません。**

> **なぜ auto にしないのか**: auto では、Omnigent がスキーマ・テーブル・AI Search などを作るコマンドが、理由を示されずに拒否されます。
> さらに auto では、`databricks *` や `python3 *` のような広い許可ルールも効かなくなるため、許可ルールを足しても解決しません。

> **ハンズオンの最後まで、このセッション 1 つで作業します。** 新しいセッションを開くと、別の Sandbox（作業場所）が割り当てられ、
> このセッションで入れた設定・スキルや、置いた教材・作ったコードは引き継がれません。
> 間違えて新しいセッションを開いたときは、元のセッションに戻ります（戻れないときは、新しいセッションで手順 1 からやり直します）。

> Omnigent の中の Databricks CLI は、あなたのユーザーの権限で動きます。あなたができないこと（管理者の権限が必要な操作）は、Omnigent にもできません。

## 2. 教材を受け取る
教材は、**Omnigent の作業場所**（`/home/sandbox-agent/workspace`。コードを書く場所）と、
**Databricks のワークスペース**（ノートブックを開いて実行する場所。この README もここで開ける）の両方に置きます。

### 最初の確認ダイアログでは「Approve & don't ask again for Bash」を選ぶ
教材を展開するときに、Omnigent が Bash のコマンドを実行する許可を求めてきます（**Approval required** のダイアログ）。

| ボタン | 意味 | 選ぶか |
|---|---|---|
| Approve | このコマンドを今回だけ許可する | 次のコマンドでまた聞かれる |
| **Approve & don't ask again for Bash** | 許可し、以降は Bash のコマンドをすべて確認なしで実行する | **これを選ぶ** |
| Approve & switch to auto mode | 許可して auto に切り替える | 選ばない（auto ではリソースを作るコマンドが拒否される） |
| Reject | 許可しない | 選ばない |

「Approve & don't ask again for Bash」を選ぶと、以降のハンズオンのコマンドは確認なしで進みます（モードが「編集を承認」なので、ファイルの編集も確認なしで通ります）。

> **それでも確認が出続けるとき**: ハンズオンで使うコマンドの許可ルールを、教材の `handson/00_setup/claude_settings.json` に用意してあります。
> Omnigent に「~/.claude/settings.json に、handson/00_setup/claude_settings.json の permissions を入れてください
> （あれば allow に足して、defaultMode を acceptEdits にする。ほかの設定は消さない）。入れたら /permissions で反映されたことを確かめてください」と頼みます。

### 設定ファイル `handson/settings.json`
環境や参加者によって変わる値は、すべて `handson/settings.json` に入っています。ノートブックもプロンプトも、この値を読みます。
値は Omnigent に入れてもらいます。参加者が自分で決めて入れるのは、講師から案内されたカタログの名前だけです（手順 5）。

| 区分 | 項目 | 入れる人 |
|---|---|---|
| `instructor` | ワークスペースの URL・カタログ・SQL ウェアハウス・共有スキーマ・AI Search のエンドポイント・基盤モデル | 参加者が手順 5 で入れる（カタログは講師の案内、SQL ウェアハウスと URL は Omnigent が調べる）。それ以外は既定のまま |
| `participant` | `user_email`（自分のメールアドレス）・`materials_folder`（教材のフォルダ名） | Omnigent が手順 2 で入れる |

受け取り方は 2 通りあります。講師の案内に従って、どちらかを選びます。

| | 基本: ZIP から | 別の方法: GitHub から |
|---|---|---|
| 使う場面 | 通常はこちら | 講師から GitHub のリポジトリを案内されたとき |
| 教材の置き場所 | 講師から受け取った ZIP（`agent-handson-main.zip`） | GitHub のリポジトリ（非公開） |
| 教材のフォルダ名（`materials_folder`） | `agent-handson-main` | `agent-handson` |

以降、ワークスペースに置いた `<教材のフォルダ>/handson/` を「自分の handson フォルダ」と呼びます。

### 基本: ZIP から
1. Omnigent のチャットの入力欄で、ファイルを添付するボタンから、講師から受け取った ZIP（`agent-handson-main.zip`）を選ぶ
2. ZIP を添付したまま、次のメッセージを送る（そのまま送れます。書き換える箇所はありません）。これがセッションの最初のメッセージです

```
添付した ZIP（ハンズオンの教材）を展開して、作業場所とワークスペースの両方に置いてください。
1. ZIP を /home/sandbox-agent/workspace に展開し、
   /home/sandbox-agent/workspace/agent-handson-main/handson/ フォルダがあることを確かめる。
2. databricks current-user me で私のメールアドレスを調べ、handson/settings.json の participant.user_email に入れる。
   participant.materials_folder は agent-handson-main のままにする。
3. 展開したフォルダを、Databricks CLI で私のワークスペースに取り込む。
   取り込み先は /Workspace/Users/<user_email>/<materials_folder>（どちらも settings.json の participant の値）。
4. 取り込み先に handson/00_setup/00_check_config ができたことを確かめ、取り込み先のパスを教える。
```

> **ZIP を添付できないとき**: 講師が共有の Volume に同じ ZIP を置いている場合は、1 の代わりに次を頼みます。
> 「Databricks CLI で、共有の Volume にある agent-handson-main.zip を /home/sandbox-agent/workspace にコピーして展開してください。
> Volume は /Volumes/<カタログ>/<共有スキーマ>/materials/ で、カタログと共有スキーマは、ZIP の中の handson/settings.json の
> instructor.catalog と instructor.shared_schema です。講師から案内された値を使ってください」

### 別の方法: GitHub から
講師から、教材のリポジトリの URL を案内されたときの方法です。次のメッセージの `<...>` を、講師の案内に置き換えて送ります。

```
次の Git リポジトリを、/home/sandbox-agent/workspace の下にクローンしてください。
<講師から案内されたリポジトリの URL>
クローンしたら、次をしてください。
1. /home/sandbox-agent/workspace/agent-handson/handson/ フォルダがあることを確かめる。
2. databricks current-user me で私のメールアドレスを調べ、handson/settings.json の participant.user_email に入れる。
   participant.materials_folder は agent-handson にする。
3. フォルダを、Databricks CLI で私のワークスペースに取り込む。
   取り込み先は /Workspace/Users/<user_email>/<materials_folder>（どちらも settings.json の participant の値）。
4. 取り込み先に handson/00_setup/00_check_config ができたことを確かめ、取り込み先のパスを教える。
```

> Omnigent からリポジトリにアクセスするには、Sandbox から GitHub に接続できる必要があります。クローンできないときは、ZIP の方法に切り替えます。

## 3. Databricks のエージェントスキルを入れる
Omnigent の中では Claude Code が動いています。Databricks の **エージェントスキル**（[Agent skills for AI coding assistants](https://docs.databricks.com/aws/en/agent-skills/)）を入れておくと、
Claude Code が AI Search・Model Serving・MLflow の評価・ジョブなどの正しい作り方を参照しながらコードを書くので、ぐっと作業が楽になります。
次の **A（プロンプト）** を送ります。プロンプトを打つのが手間な方は、**B（シェル）** でも入れられます。

### A. Omnigent にプロンプトで頼む（おすすめ）

```
Databricks のエージェントスキルを、この環境の Claude Code に入れてください。
1. databricks --version で CLI のバージョンを確かめる。aitools コマンドがない（databricks aitools --help が失敗する）
   ほど古ければ、Databricks CLI を最新に更新する。
2. databricks aitools install --agents claude-code --scope global を実行する。
3. databricks aitools list で、入ったスキルの一覧を表示する。
4. 入ったスキルの名前と、それぞれ何に使えるかを 1 行ずつ表にまとめる。
```

### B. シェルでコマンドを打つ
Omnigent の画面を **シェル** に切り替えて、次を実行します。

```bash
databricks --version                     # aitools コマンドがない古い CLI なら、下の 1 行で更新する
# curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sudo sh

databricks aitools install --agents claude-code --scope global
databricks aitools list                  # 入ったスキルを確かめる
```

### 入れたら、リロードして反映させる
入れたスキルは、そのままでは読み込まれません。次の順で反映させます。
1. Omnigent の画面を、チャットから **シェル** の画面に切り替える
2. 次のコマンドを打つ（スキルを含めて読み込み直される）

   ```
   /reload-plugins
   ```

3. チャットの画面に戻り、**同じセッションのまま** 手順 4 に進む

## 4. 作業のルールを伝える
Omnigent に次を送ります（そのまま送れます）。

```
これから Databricks のハンズオンを行います。教材は /home/sandbox-agent/workspace の下の、
handson/settings.json の participant.materials_folder のフォルダの handson/ にあります。
handson/README.md と各 Step の README.md を読み、全体の流れを把握してください。

作業のルール:
- 環境や私によって変わる値（ワークスペース・カタログ・スキーマ・メールアドレス・エンドポイント名など）は、
  プロンプトに書いていなくても、必ず handson/settings.json と handson/_config.py の決め方から求めてください。
- 私が作ってほしいコードは handson/my_work/ に置いてください。
- ファイルの形は次のとおりにしてください。
  - エージェント本体（LangGraph のグラフ・採点基準・Memory の読み書き）は、普通の Python ファイル（.py）にする。
    先頭に "# Databricks notebook source" を付けない（ノートブックにしない。ほかのファイルから import するため）。
  - エージェントを読み込んで動かす・評価する・デプロイするコードと、データの準備・ジョブのタスクは、
    Databricks のノートブックにする（ソース形式。先頭が "# Databricks notebook source"、セルの区切りは
    "# COMMAND ----------"、説明は日本語の Markdown セル）。
- 作ったファイルは、Databricks CLI で私のワークスペースの handson フォルダに反映してください。
  反映先は /Workspace/Users/<user_email>/<materials_folder>/handson/my_work/（settings.json の participant の値）。
  例: databricks workspace import-dir handson/my_work <反映先> --overwrite
  （先頭が "# Databricks notebook source" の .py はノートブックとして、それ以外の .py はファイルとして取り込まれます）
読み込みが終わったら、全体の流れを 5 行で要約してください。
あわせて、Databricks のエージェントスキル（databricks-core など）が使える状態かも教えてください。
```

## 5. 設定ファイルに、カタログと SQL ウェアハウスを入れる
Omnigent の作業場所にある `handson/settings.json` の `instructor` に、このハンズオンで使うカタログと SQL ウェアハウスを入れます。
カタログは講師から案内された名前を使います。SQL ウェアハウスとワークスペースの URL は、Omnigent に調べて入れてもらいます。
次のメッセージの `<講師から案内されたカタログ>` だけを置き換えて送ります。

```
handson/settings.json の instructor に、このハンズオンで使う値を入れてください。
1. catalog に <講師から案内されたカタログ> を入れる。databricks catalogs get でそのカタログがあり、私が使えることを確かめる。
2. warehouse_id に、私が使える SQL ウェアハウスの ID を入れる。databricks warehouses list で調べ、
   1 つしかなければそれを、複数あれば名前・種類（サーバーレスか）・状態の一覧を見せて、私に選ばせる。
3. workspace_url に、いまの Databricks CLI の接続先のワークスペースの URL を入れる。
4. ほかの項目（shared_schema・ai_search_endpoint・基盤モデル）は既定のままにする。llm_endpoint・extract_llm_endpoint・
   embedding_endpoint の基盤モデルが、databricks serving-endpoints get でワークスペースにあることを確かめる。
5. 書き換えた settings.json を、ワークスペースの取り込み先（/Workspace/Users/<user_email>/<materials_folder>/handson/settings.json）
   にも上書きで反映する。
6. handson/_config.py の決め方で、私のスキーマ名・共有のインデックス名・Memory の名前・エンドポイント名・エクスペリメントの
   パスを求めて、表にして見せる。
```

次のような表が返ってくれば完了です。

| 項目 | 例 |
|---|---|
| 自分のスキーマ | `<カタログ>.agent_handson_taro_yamada` |
| 共有のインデックス | `<カタログ>.agent_handson_shared.reference_case_index` |
| Memory | `<カタログ>.agent_handson_taro_yamada.agent_memory` |
| エンドポイント | `scoring-agent-taro-yamada` |
| エクスペリメント | `/Users/taro.yamada@example.com/agent_handson_scoring` |

スキーマ・エンドポイント・エクスペリメントは参加者ごとに分かれています。ほかの参加者のものとは名前がぶつかりません。
過去の受注事例のインデックスだけは、全員で 1 つを共有します（手順 6 で代表者が作ります）。

> 講師が `settings.json` に値を入れた ZIP を配った場合は、この手順は値の確認だけになります（1・2 で入っている値をそのまま確かめる）。

## 6. 全員で使う AI Search を作る（代表者 1 名だけ）
過去の受注事例のテーブル、AI Search のエンドポイント、インデックスを共有スキーマ（`agent_handson_shared`）に作り、参加者全員が読めて検索できるように権限を付けます。

| やり方 | 手順 |
|---|---|
| **基本: プロンプト** | [shared/prompt_shared_setup.md](shared/prompt_shared_setup.md) のプロンプトを、代表者の Omnigent に送る |
| うまくいかないとき: ノートブック | [shared/00_shared_setup](shared/00_shared_setup.py) を開いて **すべて実行** する（同じものができる） |

インデックスがオンラインになるまで 10 分ほどかかります。できたら代表者は、参加者全員に「できた」と伝えます。
確かめ方: **カタログ** → `agent_handson_shared` → `reference_case_index` を開き、**検索** で「病院 電子カルテ 人手不足」と入れて RC03 が一番上に来ること。
