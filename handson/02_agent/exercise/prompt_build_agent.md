# Omnigent に送るプロンプト（Step 2 エージェント本体を作る）

採点基準（どの観点を何点にするか）は業務の決めごとなので、できあがったもの（`02_agent/solution/rubric.py`）をそのまま使います。
エージェントの処理（LangGraph のグラフ）を、Omnigent に `agent.py` として作ってもらいます。Memory の読み書き（`memory.py`）と動作確認のノートブックは、用意したものを使います。

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

**このプロンプトで頼んでいること**: 1 回目の設計で、エージェント本体（`agent.py`）だけを作ってもらい、用意してある動作確認のノートブックで動かしてもらう。
採点基準（`rubric.py`）と Memory の読み書き（`memory.py`）、動作確認のノートブック（`solution/02_try_agent`）は、用意したものをそのまま使います。

```
## やりたいこと
さきほどの設計で、エージェント本体 handson/my_work/agent.py を作ってください。

## 用意してあるもの（書き直さない）
- handson/02_agent/solution/rubric.py と memory.py を、handson/my_work/ にコピーして使う
- 動作確認は、用意してあるノートブック handson/02_agent/solution/02_try_agent.py をそのまま使う。
  ウィジェット agent_dir に ../../my_work を渡すと、my_work の agent.py を読み込んで 1 社を採点する

## 決まりごと
- agent.py は普通の Python ファイルにする（先頭に "# Databricks notebook source" を付けない）
- 02_try_agent が読み込めるよう、最後に AGENT = <ResponsesAgent のインスタンス> と mlflow.models.set_model(AGENT) を書く
- rubric.py と memory.py の関数を使って組み立てる（同じ処理を agent.py に書き直さない）
- 設定は環境変数（HANDSON_CATALOG・HANDSON_SCHEMA・HANDSON_CASE_INDEX・HANDSON_LLM_ENDPOINT）から読む
- LLM は ChatDatabricks、AI Search は VectorSearchRetrieverTool（どちらも databricks_langchain）を使う
- 入出力は handson/README.md の「スコアリングエージェントの仕様」のとおりにする
- 企業特性の JSON がない入力（Review App で普通に質問された場合など）には、エラーにせず、
  エージェントの説明と入力の例を返す

## 気をつけること
- LLM は今日の日付を知らないので、各観点の入力に「今日の日付」（日本時間）を入れる
- 書いたら、python3 -m py_compile で構文を確かめ、使う関数が handson/requirements.txt のバージョンにあることを確かめる

## 参考にするもの
- 仕様: handson/README.md の「スコアリングエージェントの仕様」、handson/02_agent/README.md の「エージェントの構成」

## できたら
ワークスペースに反映して、ワークスペースの
/Workspace/Users/<user_email>/<materials_folder>/handson/02_agent/solution/02_try_agent を、
ウィジェット agent_dir=../../my_work で実行してよいか聞いてください
（bash handson/tools/run_notebook.sh <ノートブック> '{"agent_dir": "../../my_work"}'）。
完了の条件: 02_try_agent が最後まで動き、1 社の採点結果（score_result）が表示されること。
1 回直しても動かないときは、それ以上直さずに私に知らせてください（模範解答の agent.py に切り替えて先に進みます）。
```

## 動かしてみて、うまくいかないとき

Omnigent が実行したときは、エラーを見て自分で直してくれます。自分で実行したときは、エラーの全文と一緒に次のように頼みます。

```
02_try_agent を実行したら、次のエラーになりました。原因を調べて my_work/agent.py を直してください。
直したら、どこをなぜ直したかを 3 行で説明してください。
<エラーの全文>
```
