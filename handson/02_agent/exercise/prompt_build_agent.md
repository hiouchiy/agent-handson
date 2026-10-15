# Omnigent に送るプロンプト（Step 2 エージェントをゼロから作る）

採点基準（どの観点を何点にするか）は業務の決めごとなので、できあがったもの（`02_agent/solution/rubric.py`）をそのまま使います。
エージェントの処理（LangGraph のグラフ・AI Search・Memory）を Omnigent に作ってもらいます。

プロンプトは 2 回に分けて送ります。1 回目でグラフの設計を確かめてから、2 回目で作ってもらうと、意図とずれにくくなります。

## 1 回目: 設計を確かめる

**このプロンプトで頼んでいること**: エージェントの処理の流れ（LangGraph のグラフ）を、コードを書く前に設計して見せてもらう。

```
## やりたいこと
handson/README.md の「スコアリングエージェントの仕様」を満たすエージェントを、LangGraph で作りたいです。
まずはコードを書かずに、グラフの設計を見せてください。

## 処理の流れ
1. prepare: AI Search で過去の受注事例を 1 回だけ検索する。Managed Agent Memory から、共通ルール（scope "shared"）・
   観点別のルール（scope "rubric_<観点>"）・会社別の記憶（scope "<会社ID>"）を読む
2. score_axis: 5 観点と関係性の補正の 6 つを、LangGraph の Send で同時に採点する。
   段階と点数が基準に合わなければ、理由を伝えて 1 回だけやり直させる
3. 6 つがそろったら分岐する: どれかが基準に合わなければ fail（点数を出さない）、合えば summarize
4. summarize: 確定した点数を変えずに、評価コメント・次のアクション・根拠を書かせる
5. assemble: 合計・Tier・確からしさをプログラムで計算する（LLM に計算させない）
6. save_history: custom_inputs.save_history が true のときだけ、採点の結果を会社別の記憶に書き込む

## 決まりごと
- 採点基準は handson/02_agent/solution/rubric.py をそのまま使う（handson/my_work/rubric.py にコピーする）。
  rubric.py の関数（プロンプトを作る関数・出力を確かめる関数・合計を計算する関数）を使って組み立てる

## できたら
ノードと辺の一覧、状態（State）の項目、各ノードの入出力を、表にして見せてください。
```

## 2 回目: 作ってもらう

**このプロンプトで頼んでいること**: 1 回目の設計で、エージェント本体（Python ファイル 2 つ）と、動作確認のノートブックを作ってもらう。

```
## やりたいこと
さきほどの設計で、エージェントを作ってください。

## 作るもの
| ファイル | 形 | 中身 |
|---|---|---|
| handson/my_work/memory.py | Python ファイル | Managed Agent Memory の読み書き（scope の記憶を全部読む・1 件書き込む） |
| handson/my_work/agent.py | Python ファイル | LangGraph のグラフと、MLflow の ResponsesAgent（Model Serving の入出力） |
| handson/my_work/02_try_agent.py | ノートブック | agent.py を読み込んで 1 社を採点し、トレースを見る |

## 決まりごと
- memory.py と agent.py は普通の Python ファイルにする（先頭に "# Databricks notebook source" を付けない）
- 設定は環境変数（HANDSON_CATALOG・HANDSON_SCHEMA・HANDSON_CASE_INDEX・HANDSON_LLM_ENDPOINT）から読む。
  02_try_agent では、これらに _config.py の値を入れてから agent.py を読み込む
- LLM は ChatDatabricks、AI Search は VectorSearchRetrieverTool（どちらも databricks_langchain）を使う
- 入出力は handson/README.md の「スコアリングエージェントの仕様」のとおりにする
- 企業特性の JSON がない入力（Review App で普通に質問された場合など）には、エラーにせず、
  エージェントの説明と入力の例を返す
- ライブラリは handson/requirements.txt のバージョンに合わせる

## 気をつけること
- Model Serving の中では、Memory を「呼び出したユーザー本人の資格情報（OBO）」で読む。トークンはリクエストごとに取り、
  取れなければエラーにする（ほかの資格情報に切り替えない）
- LLM は今日の日付を知らないので、各観点の入力に「今日の日付」（日本時間）を入れる
- 02_try_agent では、エクスペリメントのトレースを _config.py の TRACE_TABLE（Delta テーブル）に同期する
  （mlflow.tracing.archival.enable_databricks_trace_archival。2 回目以降の実行で「すでに有効」のエラーになっても止めない）
- 02_try_agent は、模範解答（handson/02_agent/solution/02_try_agent.py）と同じセルの構成にする。
  トレースをコードで読み直さない（トレースの中身は、私がエクスペリメントの画面で確かめる）

## 参考にするもの
- 仕様: handson/README.md の「スコアリングエージェントの仕様」、handson/02_agent/README.md の「エージェントの構成」
- Memory の API と OBO の書き方: handson/02_agent/solution/memory.py
- 動作確認のノートブックの流れ: handson/02_agent/solution/02_try_agent.py

## できたら
ワークスペースに反映して、02_try_agent を実行してよいか聞いてください。
完了の条件: 02_try_agent が最後まで動き、1 社の採点結果（score_result）が表示されること。
```

## 動かしてみて、うまくいかないとき

Omnigent が実行したときは、エラーを見て自分で直してくれます。自分で実行したときは、エラーの全文と一緒に次のように頼みます。

```
my_work/02_try_agent を実行したら、次のエラーになりました。原因を調べて直してください。
直したら、どこをなぜ直したかを 3 行で説明してください。
<エラーの全文>
```
