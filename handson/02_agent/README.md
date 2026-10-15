# Step 2 LangGraph でエージェントを作り、トレースを見る（40 分）

## このステップでやること
1. Omnigent に、スコアリングエージェントの本体（`agent.py`）を作ってもらう（バイブコーディング）。採点基準・Memory の読み書き・動作確認のノートブックは用意したものを使う
2. ノートブックで 1 社を採点し、MLflow のトレースで処理の中身を見る
3. トレースを Unity Catalog の Delta テーブルに同期し、SQL で確かめる

## エージェントの構成

```
START → prepare ─(Send ×6)─▶ score_axis ─▶ collect ─┬─▶ summarize → assemble ─┬─▶ save_history → END
         │                   （5 観点＋補正を同時に）  │                         └─▶ END（save_history=false）
         │                                            └─▶ fail → END（基準に合わない採点があった）
         ├ AI Search: 過去の受注事例を 1 回検索
         └ Memory: 共通ルール・観点別ルール・会社別の記憶を読む
```

| ファイル | 形 | 内容 |
|---|---|---|
| `rubric.py` | Python ファイル | 採点基準（観点ごとの段階と点数範囲、プロンプト、合計・Tier の計算）。**業務の決めごと**。業務の人が読む表は [rubric.md](rubric.md) |
| `memory.py` | Python ファイル | Managed Agent Memory の読み書き（Model Serving では呼び出したユーザー本人の資格情報で読む） |
| `agent.py` | Python ファイル | LangGraph のグラフと、MLflow の ResponsesAgent（Model Serving の入出力） |
| `02_try_agent` | ノートブック | `agent.py` を読み込んで 1 社を採点し、トレースを見る（用意したもの `solution/02_try_agent` を使う） |

このうち Omnigent に作ってもらうのは `agent.py` だけです。`rubric.py` と `memory.py` は `solution/` から `my_work/` にコピーし、`02_try_agent` は `solution/` のものをそのまま使います。

> **採点基準について**: 採点基準は本来、業務部門の持ち物で、Excel や Word などのドキュメントで作って直すものです。
> 本番では、そのドキュメントを Unity Catalog の Volume などに置き、エージェントが読み込んでプロンプトを組み立てます。
> このハンズオンでは時間の都合で、その中身を書き写した `rubric.py` を使います。業務の人が読む形の表は [rubric.md](rubric.md) です
> （`rubric.py` から `tools/make_rubric_doc.py` で作ったもの）。

エージェント本体は Python ファイルにして、ノートブックから `import` して使います。同じファイルを、Step 3 の評価と
Step 4 のデプロイでもそのまま使います（Model Serving にも、このファイルがそのまま載ります）。

**LLM にさせること・させないこと**
- させる: 観点ごとに「段階を選び、範囲の中で点数を決め、根拠を書く」。まとめの文章を書く
- させない: 足し算・Tier の判定（プログラムで計算する）。会社を選ぶこと（会社IDは呼び出し側が決める）
- 段階と点数が合わない（例: 段階 3 なのに 25 点）ときは、プログラムが見つけて 1 回だけやり直させる

## 演習

### 2-1. エージェントを作る（Omnigent）
[exercise/prompt_build_agent.md](exercise/prompt_build_agent.md) のプロンプトを、2 回に分けて Omnigent に送ります。

### 2-2. 動かしてトレースを見る（Omnigent・Databricks の画面）
1. 用意してあるノートブック `02_agent/solution/02_try_agent` を、ウィジェット `agent_dir` を `../../my_work` にして実行する
   （`my_work` の `agent.py` を読み込みます。ライブラリのインストールを含めて 2〜3 分）。実行の仕方は 2 通りあります。
   - **A（おすすめ）: Omnigent に実行してもらう** — Omnigent が「このまま実行しますか？」と聞いてくるので「はい」と答える。
     終わると、結果の要点と **実行の画面の URL** が返ってくるので、URL を開いてセルの出力を見る
   - **B: 自分で実行する** — ワークスペースの自分の handson フォルダの `02_agent/solution/02_try_agent` を開き、ウィジェット `agent_dir` に `../../my_work` を入れて、右上で **サーバーレス** を選んで **すべて実行** する
2. 採点の結果（`score_result`）が表示されることを確認する
3. 実行の画面のセルの下に出るトレース、または **エクスペリメント** → `agent_handson_scoring` → **トレース** を開き、次を確かめる
   - `prepare` の中の `search_reference_cases`（AI Search）: どの事例が見つかったか
   - `score_axis` が 6 つ並んで、同時に動いていること
   - 各 `ChatDatabricks` に渡したプロンプトと、LLM の返事
4. 最後のセルで、同じトレースが `scoring_traces` テーブルに入っていることを確かめる。
   同期は 15 分ごとなので、テーブルがまだない・空のときは、Step 3 のあとでもう一度実行する

> **トレースの保存先**: トレースは MLflow のエクスペリメントに入り、15 分ごとに自分のスキーマの Delta テーブル（`scoring_traces`）に同期されます。
> 同期は、ノートブックで有効にした自分の権限で動くジョブが行います。Step 4 でデプロイしたエージェントも、資格情報を持たずにこのエクスペリメントへトレースを送るだけで、同じテーブルに入ります。
> Delta テーブルなので、Unity Catalog の権限で管理でき、SQL で集計したり、ダッシュボードに出したりできます。1 トレースが 1 行で、各処理（スパン）は `spans`、フィードバックや評価は `assessments` に配列で入ります。

### 2-3. 余裕があれば
入力の企業特性を書き換えて、点数がどう変わるかを試します（例: `existing_relationship` を「競合の MSS を導入済み」にする）。

## うまくいかないとき
- `SQL warehouse ID is required for accessing traces in UC tables` と出る: 以前に、トレースの保存先を Unity Catalog にした
  同じ名前のエクスペリメント（`agent_handson_scoring`）が残っています。**エクスペリメント** の画面で、そのエクスペリメントの名前を
  変えて（例: `agent_handson_scoring_old`）から、もう一度実行します。
- Omnigent が 1 回直しても動かないとき: それ以上は直さず、模範解答 [solution/](solution/) の `agent.py` を `my_work/` にコピーして先に進むか、
  [solution/02_try_agent](solution/02_try_agent.py) をそのまま実行します（ウィジェット `agent_dir` が模範解答のフォルダを指しています）。
