# Omnigent に送るプロンプト（Step 3 オフライン評価）

## 評価のノートブックを動かす

**このプロンプトで頼んでいること**: 用意してある評価のノートブック（`solution/03_evaluate`）の中身を説明してもらい、Step 2 で作ったエージェントでそのまま実行してもらう。
評価のしくみ（データセットの登録・スコアラー・結果の表）は誰が書いても同じになるので、用意したものを使います。

```
## やりたいこと
Step 3 の評価は、用意してあるノートブック handson/03_evaluation/solution/03_evaluate.py を、書き直さずにそのまま使います。

1. このノートブックの評価データ（handson/03_evaluation/eval_dataset.json）と、4 つのスコアラーが何を確かめるかを、表にして説明してください
2. 説明が終わったら、ワークスペースの
   /Workspace/Users/<user_email>/<materials_folder>/handson/03_evaluation/solution/03_evaluate を、
   ウィジェット agent_dir=../../my_work（Step 2 で作ったエージェント）で実行してよいか聞いてください
   （bash handson/tools/run_notebook.sh <ノートブック> '{"agent_dir": "../../my_work"}'）

## 決まりごと
- ノートブックは書き直さない。失敗したときは、原因を調べて教えてください（直す前に私に聞く）

## できたら
完了の条件: 評価が最後まで動き、評価データごとに、どのスコアラーが OK／NG かが表示されること（最初は NG が出ます）。
```

## 直すとき（例）

**このプロンプトで頼んでいること**: NG の原因が分かったあとで、直したい内容を伝えて直してもらい、もう一度評価してもらう。

```
## やりたいこと
評価で E00X が NG になったので、直してもう一度評価してください。

## NG の理由
<Genie Code で調べてわかったこと>

## 直したいこと
<例: 採点基準の〇〇を△△に変える>

## 決まりごと
- 直すのは handson/my_work/ のファイル（rubric.py など）か、Memory だけ。評価のノートブックは書き直さない
- 採点基準（rubric.py）を変えた場合は RUBRIC_VERSION を 1 つ上げる
- Memory に記憶を足すときは、用意してあるノートブック handson/03_evaluation/solution/03_add_memory.py を使う

## できたら
どのファイルのどこを変えたかを教えてから、ワークスペースに反映して、評価（solution/03_evaluate を agent_dir=../../my_work で）を
もう一度実行してよいか聞いてください。
```
