# Step 3 オフライン評価で品質を上げる（40 分）

## このステップでやること
1. 評価データ（3 件）を MLflow の **評価データセット** として登録する
2. スコアラー（採点の物差し）を決めて評価し、エクスペリメントで結果を見る
3. **Genie Code** で、NG になった理由を調べる
4. 原因に合った直し方で直し、もう一度評価して **全件 OK** にする

## 評価データ
[eval_dataset.json](eval_dataset.json) の 3 件です。1 件は「入力（企業特性）」と「期待値（業務部門が期待する答え）」の組です。

| 期待値のキー | 意味 |
|---|---|
| `expected_tier` | 期待する Tier |
| `expected_adjustment_min` / `expected_adjustment_max` | 関係性の補正の期待する範囲 |
| `expected_axis_levels` | 観点ごとの期待する段階（例: `{"size_budget": 4}`） |
| `guidelines` | 文章で書いた合格条件（LLM ジャッジが判定する） |

> **最初は NG が出ます。** 評価データは、いまのエージェントでは満たせない業務部門の期待を含んでいます。
> NG の原因はそれぞれ違い、直す場所も違います。

## スコアラー

| スコアラー | 種類 | 見ること |
|---|---|---|
| `output_schema_valid` | コード | 出力に必要な項目がそろっているか |
| `axis_levels_valid` | コード | 観点ごとの点数が、選んだ段階の範囲に入っているか |
| `tier_matches` | コード（期待値あり） | Tier が期待どおりか |
| `adjustment_in_expected_range` | コード（期待値あり） | 関係性の補正が期待する範囲か |
| `axis_levels_match` | コード（期待値あり） | 観点ごとの段階が期待どおりか |
| `meets_guidelines` | LLM ジャッジ（期待値あり） | 文章の合格条件を満たしているか |

期待値がない評価データでは、そのスコアラーは判定しません。

## 演習

### 3-1. 評価のノートブックを作って実行する（Omnigent → Databricks の画面）
1. [exercise/prompt_evaluate.md](exercise/prompt_evaluate.md) のプロンプトを Omnigent に送る
2. できた `my_work/03_evaluate` を開いて **すべて実行** する
3. **エクスペリメント** → `agent_handson_scoring` → **評価** タブで、いま作られた評価を開く
4. 評価データごとに、どのスコアラーが NG かを見る。NG の行を開くと、スコアラーの理由とトレースが見られる

### 3-2. NG の理由を Genie Code で調べる（Databricks の画面）
評価の画面やトレースを開いたまま、右上の **Genie Code**（Assistant）を開いて質問します。
質問の例は [exercise/genie_code_questions.md](exercise/genie_code_questions.md) にあります。

調べるときの観点:
- エージェントの出力（段階・点数・根拠）は、採点基準（`rubric.py`）どおりか
- 採点基準どおりなのに NG なら、**評価データの期待と採点基準のどちらが正しいか**（業務の判断）
- エージェントが知らない情報（CRM にない事情）が必要ではないか
- 文章の書き方の指示（プロンプト）が足りないのではないか

### 3-3. 直してもう一度評価する（Omnigent・Databricks の画面）
原因ごとに、直す場所を選びます。

| 直す場所 | どんなときに直すか |
|---|---|
| Managed Agent Memory | CRM などのデータにない、会社ごとの事情を採点に入れたいとき |
| 採点基準（`rubric.py` の段階・点数・補足） | 業務部門の判断と、採点基準の決めごとが違うとき |
| プロンプト（`rubric.py` の `SUMMARY_PROMPT` など） | 出力の文章に、書いてほしいことが書かれていないとき |

採点基準を変えたら `RUBRIC_VERSION` を上げます（評価の結果を版ごとに比べるため）。
直したら `my_work/03_evaluate` をもう一度実行し、**全件 OK** になることを確かめます。
エクスペリメントの **評価** タブで、直す前と後の評価を並べて比べてみます。

## うまくいかないとき
- 評価: [solution/03_evaluate](solution/03_evaluate.py)（ウィジェット `agent_dir` を `../../my_work` にすると自分のエージェントを評価できる）
- 直し方の模範解答: [solution/03_add_memory](solution/03_add_memory.py)（Memory）と [solution/fixed/](solution/fixed/)（直した後のエージェント）
