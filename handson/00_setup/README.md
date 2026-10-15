# Step 0 準備（15 分）

## このステップでやること

| # | やること | 誰が |
|---|---|---|
| 1 | Omnigent を起動し、権限のモードを「編集を承認」にする | 全員 |
| 2 | 教材を受け取る（Omnigent の作業場所に展開する）。最初の確認で、以降の Bash を確認なしにする | 全員 |
| 3 | 設定ファイル（`settings.json`）にカタログと SQL ウェアハウスを入れてから、教材をワークスペースに取り込む | 全員 |
| 4 | Databricks のエージェントスキルを入れて、リロードする | 全員 |
| 5 | 作業のルールを Omnigent に伝える（変えたファイルは毎回ワークスペースにも反映する・ノートブックは Omnigent が実行する・実行の前にコードを確かめる） | 全員 |
| 6 | 全員で使う AI Search（エンドポイントとインデックス）があることを確かめる（事前準備で作ってある） | 全員 |

教材を最初に受け取るので、手順 3 以降は、教材の中のこの README を開いて、プロンプトをコピーしながら進められます。

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
まず、教材を **Omnigent の作業場所**（`/home/sandbox-agent/workspace`）に置きます。
**Databricks のワークスペース**（ノートブックを開いて実行する場所）への取り込みは、手順 3 で `settings.json` を編集してから行います
（先に取り込むと、あとで編集した内容がワークスペース側に入らないため）。

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
値は Omnigent に入れてもらいます。参加者が自分で決めて入れるのは、講師から案内されたカタログの名前だけです（手順 3）。

| 区分 | 項目 | 入れる人 |
|---|---|---|
| `instructor` | ワークスペースの URL・カタログ・SQL ウェアハウス・共有スキーマ・AI Search のエンドポイント・基盤モデル | 参加者が手順 3 で入れる（カタログは講師の案内、SQL ウェアハウスと URL は Omnigent が調べる）。それ以外は既定のまま |
| `participant` | `user_email`（自分のメールアドレス）・`materials_folder`（教材のフォルダ名） | Omnigent が手順 2 で入れる |

受け取り方は 2 通りあります。講師の案内に従って、どちらかを選びます。

| | 基本: ZIP から | 別の方法: GitHub から |
|---|---|---|
| 使う場面 | 通常はこちら | 講師から GitHub のリポジトリを案内されたとき |
| 教材の置き場所 | 講師から受け取った ZIP（`agent-handson-main.zip`） | GitHub のリポジトリ（非公開） |
| 教材のフォルダ名（`materials_folder`） | `agent-handson-main` | `agent-handson-main`（ZIP と同じ名前になるよう、このフォルダ名でクローンする） |

以降、ワークスペースに置いた `<教材のフォルダ>/handson/` を「自分の handson フォルダ」と呼びます。

### 基本: ZIP から
1. Omnigent のチャットの入力欄で、ファイルを添付するボタンから、講師から受け取った ZIP（`agent-handson-main.zip`）を選ぶ
2. ZIP を添付したまま、次のメッセージを送る（そのまま送れます。書き換える箇所はありません）。これがセッションの最初のメッセージです

```
## やりたいこと
添付した ZIP（ハンズオンの教材）を、作業場所に展開してください。ワークスペースへの取り込みは、まだしません。

## やること
1. ZIP を /home/sandbox-agent/workspace に展開する
2. databricks current-user me で私のメールアドレスを調べ、handson/settings.json の participant.user_email に入れる
   （participant.materials_folder は agent-handson-main のまま）

## できたら
/home/sandbox-agent/workspace/agent-handson-main/handson/ ができたことと、入れたメールアドレスを教えてください。
```

> **ZIP を添付できないとき**: 講師が共有の Volume に同じ ZIP を置いている場合は、1 の代わりに次を頼みます。
> 「Databricks CLI で、共有の Volume にある agent-handson-main.zip を /home/sandbox-agent/workspace にコピーして展開してください。
> Volume は /Volumes/<カタログ>/<共有スキーマ>/materials/ で、カタログと共有スキーマは、ZIP の中の handson/settings.json の
> instructor.catalog と instructor.shared_schema です。講師から案内された値を使ってください」

### 別の方法: GitHub から
講師から、教材のリポジトリの URL を案内されたときの方法です。次のメッセージの `<...>` を、講師の案内に置き換えて送ります。

```
## やりたいこと
次の Git リポジトリを、作業場所にクローンしてください。ワークスペースへの取り込みは、まだしません。
<講師から案内されたリポジトリの URL>

## やること
1. /home/sandbox-agent/workspace の下に、フォルダ名を agent-handson-main にしてクローンする
   （git clone <リポジトリの URL> /home/sandbox-agent/workspace/agent-handson-main。
    ZIP から展開したときと同じフォルダ名にするため。リポジトリの名前の agent-handson のままにしない）
2. databricks current-user me で私のメールアドレスを調べ、handson/settings.json の participant.user_email に入れる
   （participant.materials_folder は agent-handson-main のまま）

## できたら
/home/sandbox-agent/workspace/agent-handson-main/handson/ ができたことと、入れたメールアドレスを教えてください。
```

> **フォルダ名に注意**: そのままクローンすると、フォルダ名がリポジトリの名前（`agent-handson`）になります。ZIP から展開したときと同じ
> `agent-handson-main` にしておくと、以降の手順やプロンプトに出てくるフォルダ名（ワークスペースの取り込み先など）がそのまま使えます。
>
> Omnigent からリポジトリにアクセスするには、Sandbox から GitHub に接続できる必要があります。クローンできないときは、ZIP の方法に切り替えます。

## 3. 設定ファイルを編集してから、ワークスペースに取り込む
Omnigent の作業場所にある `handson/settings.json` の `instructor` に、このハンズオンで使うカタログと SQL ウェアハウスを入れ、
そのあとで教材をまるごとワークスペースに取り込みます。
カタログは講師から案内された名前を使います。SQL ウェアハウスとワークスペースの URL は、Omnigent に調べて入れてもらいます。
次のメッセージの `<講師から案内されたカタログ>` だけを置き換えて送ります
（`settings.json` を自分で直接編集してカタログを入れた場合は、1 を「入っているカタログを確かめる」に読み替えて送ります）。

```
## やりたいこと
handson/settings.json の instructor に、このハンズオンで使う値を入れてから、教材をワークスペースに取り込んでください。

## 入れる値
| 項目 | 入れる値 |
|---|---|
| catalog | <講師から案内されたカタログ>（そのカタログがあり、私が使えることも確かめる） |
| warehouse_id | 私が使える SQL ウェアハウスの ID（1 つしかなければそれ、複数あれば一覧を見せて私に選ばせる） |
| workspace_url | いまの Databricks CLI の接続先のワークスペースの URL |
| そのほか | 既定のまま（基盤モデルの 3 つが、ワークスペースにあることだけ確かめる） |

## そのあとにやること
教材のフォルダをまるごと、私のワークスペースの /Workspace/Users/<user_email>/<materials_folder> に取り込む
（user_email と materials_folder は settings.json の participant の値）。

## できたら
handson/_config.py の決め方で、私のスキーマ名・共有のインデックス名・Memory の名前・エンドポイント名・エクスペリメントの
パスを求めて、表にして見せてください。
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
過去の受注事例のインデックスだけは、全員で 1 つを共有します（事前準備で作ってあります。手順 6 で確かめます）。

> 講師が `settings.json` に値を入れた ZIP を配った場合は、1・2 は入っている値を確かめるだけになります。

> **あとから `settings.json` を変えたとき**: Sandbox 側の変更は、ワークスペース側には自動では入りません。
> 自分で編集したときは、Omnigent に「handson/settings.json をワークスペースに反映して」と送ります
> （Omnigent が自分でファイルを変えたときは、手順 5 の作業のルールで、毎回反映してもらいます）。

## 4. Databricks のエージェントスキルを入れる
Omnigent の中では Claude Code が動いています。Databricks の **エージェントスキル**（[Agent skills for AI coding assistants](https://docs.databricks.com/aws/en/agent-skills/)）を入れておくと、
Claude Code が AI Search・Model Serving・MLflow の評価・ジョブなどの正しい作り方を参照しながらコードを書くので、ぐっと作業が楽になります。
次の **A（プロンプト）** を送ります。プロンプトを打つのが手間な方は、**B（シェル）** でも入れられます。

### A. Omnigent にプロンプトで頼む（おすすめ）

```
## やりたいこと
Databricks のエージェントスキルを、この環境の Claude Code に入れてください。

## やること
1. databricks aitools install --agents claude-code --scope global を実行する
   （aitools コマンドがないほど Databricks CLI が古ければ、先に CLI を最新に更新する）
2. databricks aitools list で、入ったスキルを確かめる

## できたら
入ったスキルの名前と、それぞれ何に使えるかを、1 行ずつ表にして見せてください。
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

3. チャットの画面に戻り、**同じセッションのまま** 手順 5 に進む

## 5. 作業のルールを伝える
Omnigent に次を送ります（そのまま送れます）。
このハンズオンでは、Omnigent が作ったノートブックを、**Omnigent にそのまま実行してもらう** のが基本です（自分でワークスペースのノートブックを開いて実行することもできます）。
Omnigent とやり取りし続けるので、Sandbox が止まりにくくなり、失敗したときも Omnigent がエラーを見て直せます。

```
## やりたいこと
これから Databricks のハンズオンを行います。教材を読んで、全体の流れをつかんでください。
教材は /home/sandbox-agent/workspace の下の、handson/settings.json の participant.materials_folder のフォルダの handson/ にあります。
handson/README.md と、各 Step の README.md を読んでください。

## 作業のルール（ハンズオンの最後まで守ってください）
1. 設定値: 環境や私によって変わる値（ワークスペース・カタログ・スキーマ・メールアドレス・エンドポイント名など）は、
   プロンプトに書いていなくても、handson/settings.json と handson/_config.py の決め方から求める
2. 置き場所: 私が作ってほしいコードは handson/my_work/ に置く
3. ファイルの形:
   - エージェント本体（LangGraph のグラフ・採点基準・Memory の読み書き）は、普通の Python ファイル（.py）にする
     （先頭に "# Databricks notebook source" を付けない。ほかのファイルから import するため）
   - それ以外（エージェントを動かす・評価する・デプロイするコード、データの準備、ジョブのタスク）は、
     Databricks のノートブック（ソース形式）にする。セルの説明は日本語の Markdown セルで書く
4. ワークスペースへの反映: handson/ の下のファイルを作ったり変えたりしたら、毎回、Databricks CLI で
   /Workspace/Users/<user_email>/<materials_folder>/handson/ の下の同じ場所に上書きで反映する
   （例: databricks workspace import-dir handson/my_work <反映先>/my_work --overwrite）
5. ノートブックの実行: ノートブックを作ったり直したりしたら、「このまま実行しますか？」と私に聞く。
   「はい」なら handson/tools/run_notebook.sh でワークスペースのノートブックを実行し、終わるまで待つ
   （例: bash handson/tools/run_notebook.sh /Workspace/Users/<user_email>/<materials_folder>/handson/my_work/01_prepare_data）。
   終わったら、結果の要点と実行の画面の URL を教える。失敗したら、原因を調べて直し、もう一度聞く
6. コードの書き方: ノートブックの実行には数分かかるので、つまらないバグで落ちないよう、実行してよいか聞く前に次を済ませる
   - 各 Step の solution/ に同じことをする模範解答があるので、その構成と API の使い方に合わせる。
     プロンプトにない処理（結果を読み直して確かめる処理など）を足さない
   - 使う関数・引数・戻り値の形が、handson/requirements.txt のバージョンにあることを確かめる
     （分からなければ、模範解答か、そのバージョンのライブラリのソースを見る。推測で書かない）
   - None や空になりうる戻り値は、確かめてから使う
   - python3 -m py_compile で、構文の誤りがないことを確かめる
   - 失敗して直したときは、同じ種類のバグがほかの場所にないかも見直してから、もう一度聞く

## できたら
全体の流れを 5 行で要約してください。あわせて、Databricks のエージェントスキル（databricks-core など）が使える状態かも教えてください。
```

### Sandbox は、操作がないまま 10 分たつと止まる
- 止まっても、作業場所（`/home/sandbox-agent/workspace`）のファイルや、入れたスキル・設定は残ります。次にメッセージを送ると再開します。
- ノートブックを Omnigent に実行してもらえば、実行している間も Omnigent とやり取りが続くので、止まりにくくなります。
- **再開したら、まずシェルの画面で次を打ちます**（打たないと、メッセージを送ったときに `403 ... is no longer available` のエラーになります）。

  ```
  /model system.ai.claude-opus-5-5
  ```

  再開すると、使うモデルが古い名前（Opus 4.6）に戻ってしまうためです。`/model` の一覧には `system.ai.` のモデルが出てこないので、
  上のように名前を直接打ちます。そのあとチャットに戻って、もう一度メッセージを送ります（新しいセッションは開きません）。

## 6. 全員で使う AI Search があることを確かめる
過去の受注事例のテーブルと AI Search のインデックスは、全員で共有します。インデックスの作成と同期には時間がかかるので、
**ハンズオンの前に、ワークスペースの管理者（または代表者）が事前準備で作っておきます**（講師から渡す「事前準備の手順書」の手順 5）。
当日は、作ってあることを確かめるだけです。

確かめ方: **カタログ** → `<カタログ>` → `agent_handson_shared` → `reference_case_index` を開き、**検索** で「病院 電子カルテ 人手不足」と入れて
RC03 が一番上に来ること。

### 事前準備ができていなかったとき（代表者 1 名だけ）
共有スキーマ（`agent_handson_shared`）に、事例のテーブル・AI Search のエンドポイント・インデックスを作り、全員が読めて検索できるように権限を付けます。
作りたてのエンドポイントでは、インデックスの同期に **10〜15 分** かかります。その間、ほかの参加者は Step 1 の 1-1（自分のデータの準備）を先に進めます。

| やり方 | 手順 |
|---|---|
| **基本: プロンプト** | [shared/prompt_shared_setup.md](shared/prompt_shared_setup.md) のプロンプトを、代表者の Omnigent に送る |
| うまくいかないとき: ノートブック | [shared/00_shared_setup](shared/00_shared_setup.py) を実行する（同じものができる）。Omnigent に「handson/tools/run_notebook.sh で 00_setup/shared/00_shared_setup を実行して」と頼むか、ワークスペースで開いて **すべて実行** する |

できたら代表者は、参加者全員に「できた」と伝えます。
