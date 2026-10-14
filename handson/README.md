# エージェントハンズオン

法人向けセキュリティサービスの見込み顧客を、AI エージェントが 0〜100 点と Tier（A/B/C）で採点します。
この仕組みを、データの準備からエージェントの作成・評価・デプロイ・定期実行・ダッシュボードまで、3 時間で一通り作ります。

コードは、Databricks 上で動くコーディングエージェント **Omnigent** に頼んで書いてもらいます（バイブコーディング）。
AI Search のインデックスを作る、MLflow でトレースや評価の結果を見る、といった操作は Databricks の画面で行います。
Omnigent と Databricks の画面を行き来しながら、ステップごとに進めます。

## 作るもの

```
[Volume] 会社ごとのディープリサーチの結果（research/<会社ID>/research.md）
   │  Step 5 のジョブ
   ▼
 タスク1  企業特性を作る（ai_query）  ──▶ company_characteristic
   ▼
 タスク2  スコアリングエージェントを呼ぶ ──▶ scoring_response
   │        ┌──────────────── スコアリングエージェント（LangGraph, Model Serving）────────────────┐
   │        │ prepare   : AI Search で過去の受注事例を検索 ＋ Managed Agent Memory を読む          │
   │        │ score_axis: 5 観点＋関係性の補正を同時に採点（段階と点数が合わなければやり直し）     │
   │        │ summarize : 評価コメント・次のアクション・根拠                                         │
   │        │ assemble  : 合計・Tier・確からしさはプログラムで計算 → 採点の履歴を Memory に残す       │
   │        └────────────────────────────────────────────────────────────────────────────────────┘
   ▼
 タスク3  結果を Delta テーブルに書く   ──▶ customer_product_score ──▶ AI/BI ダッシュボード

 MLflow: トレース（Unity Catalog の Delta テーブルに OpenTelemetry 形式で保存）・オフライン評価・Review App
```

| 使う機能 | このハンズオンでの使い方 |
|---|---|
| AI Search（旧 Vector Search） | 過去の受注事例を、企業特性に近い順に探す |
| Managed Agent Memory | 採点のルール、会社ごとの申し送り、過去の採点の履歴を長期記憶として持つ |
| LangGraph ＋ MLflow | エージェントを組み、MLflow のモデルとして記録する |
| MLflow のトレース（Unity Catalog に保存） | エージェントの各処理を記録し、エクスペリメントと SQL の両方から見る |
| MLflow のオフライン評価 | 評価データで品質を測り、NG を直して全件 OK にする |
| Model Serving ＋ Review App | エージェントを API として公開し、人のフィードバックを集める |
| Lakeflow Jobs ＋ AI/BI ダッシュボード | 毎朝の採点を自動化し、結果を営業が見られるようにする |

## スコアリングエージェントの仕様

**入力**: 企業特性の JSON（ユーザーメッセージの本文）。会社IDは `custom_inputs.company_id` で渡す。

```json
{"input": [{"role": "user", "content": "次の企業特性をスコアリングしてください。\n{\"company_id\":\"C001\", \"industry\":\"...\", ...}"}],
 "custom_inputs": {"company_id": "C001", "save_history": true}}
```

企業特性の項目: `company_id` `company_name` `industry` `is_critical_infra` `regulated` `legacy_scale`（高/中/低）
`security_staffing`（逼迫/一部逼迫/十分）`size_class`（大/中/小）`public_exposure`（高/中/低）`recent_trigger`
`existing_relationship`（自社 CRM の要約）`key_facts`（根拠になる事実）`summary`

**出力**: `custom_outputs.score_result`

```json
{"company_id": "C001", "company_name": "...", "score": 72, "tier": "B",
 "subscores": {"need_vuln": 20, "critical_regulated": 10, "staffing_gap": 9, "size_budget": 15, "timing": 12},
 "relationship_adjustment": 0,
 "axis_details": {"need_vuln": {"level": 3, "points": 20, "evidence": ["..."], "info_missing": false}, "...": {}},
 "adjustment_detail": {"level": 0, "adjustment": 0, "evidence": ["..."]},
 "key_signals": ["..."], "matched_cases": ["RC08"], "next_action": "...",
 "confidence": "high", "rationale": "...", "rubric_version": "1.0"}
```

**採点の観点**（詳しい基準は [02_agent/solution/rubric.py](02_agent/solution/rubric.py)）

| 観点 | 満点 | 内容 |
|---|---|---|
| ① 脆弱性リスクの大きさ `need_vuln` | 30 | 古いシステム・大規模なシステム、インターネットに公開している資産 |
| ② 重要インフラ・規制業種 `critical_regulated` | 25 | 電力・通信・鉄道などの重要インフラ、金融・医療などの規制業種 |
| ③ セキュリティ人材の不足 `staffing_gap` | 15 | 専任の体制がない、外部委託の意向がある |
| ④ 企業規模・予算 `size_budget` | 15 | 従業員数・売上 |
| ⑤ 導入のきっかけ `timing` | 15 | 直近のインシデント・監査での指摘・規制強化・システム刷新 |
| 関係性の補正 `relationship_adjustment` | 0〜−15 | 競合製品がすでに入っているなど |

各観点は 4 段階で、段階ごとに点数の範囲が決まっています。LLM は「段階を選び、その範囲で点数を決め、根拠を書く」だけを行い、
合計と Tier（A: 80 以上 / B: 60〜79 / C: 60 未満）はプログラムが計算します。

## 進め方（3 時間）

| Step | 内容 | 主な画面 | 目安 |
|---|---|---|---|
| [0](00_setup/README.md) | 準備（教材の取り込み、Omnigent の起動、エージェントスキルの導入）。代表者は共有の AI Search を作る | Databricks・Omnigent | 15 分 |
| [1](01_data_ai_search/README.md) | 自分のデータを用意し、共有の AI Search で事例を検索する | Databricks・Omnigent | 20 分 |
| [2](02_agent/README.md) | LangGraph でエージェントを作り、トレースを見る | Omnigent・Databricks | 40 分 |
| [3](03_evaluation/README.md) | オフライン評価 → Genie Code で NG の原因を調べる → 直して全件 OK | Databricks・Omnigent | 40 分 |
| [4](04_deploy_review_app/README.md) | Model Serving にデプロイし、Review App で人のフィードバックを付ける | Omnigent・Databricks | 30 分 |
| [5](05_job_dashboard/README.md) | ジョブで定期実行し、結果をダッシュボードで見る | Databricks・Omnigent | 30 分 |
| — | 休憩・予備 | | 5 分 |

### ファイルの形
| 何のコードか | 形 | 例 |
|---|---|---|
| エージェント本体（LangGraph のグラフ・採点基準・Memory の読み書き） | Python ファイル（`.py`） | `agent.py`・`rubric.py`・`memory.py` |
| エージェントを読み込んで動かす・評価する・デプロイする | Databricks のノートブック | `02_try_agent`・`03_evaluate`・`04_deploy` |
| データの準備・ジョブのタスク | Databricks のノートブック | `01_prepare_data`・`task1_extract_characteristics` |

コードは Omnigent に書いてもらい、できたノートブックも **Omnigent に実行してもらう** のが基本です（`handson/tools/run_notebook.sh` を使う）。
実行の結果は、Omnigent が返す実行の画面の URL を Databricks の画面で開いて、みんなでセルの出力を見ます。自分でノートブックを開いて実行することもできます。

各 Step のフォルダには次の 2 つがあります。

- `exercise/`: 演習。Omnigent に渡すプロンプトと、Databricks の画面で行う操作
- `solution/`: 模範解答（完成したコード）。演習が進まないときは、ここをそのまま使って先に進めます

## フォルダ構成

```
handson/
├── README.md                 # このファイル
├── _config.py                # 共通の設定（カタログ・エンドポイント名など。参加者ごとの名前は自動で決まる）
├── requirements.txt          # ノートブックで入れるライブラリ（バージョン固定）
├── data/                     # ディープリサーチの結果（架空の 3 社）・過去の受注事例・自社 CRM
├── 00_setup/ … 05_job_dashboard/   # 各 Step（exercise/ と solution/）
├── tools/run_notebook.sh     # ワークスペースのノートブックを実行して、結果を表示する（Omnigent が使う）
├── my_work/                  # 参加者が Omnigent と作るコードの置き場所（最初は空）
└── instructor/               # 講師向け（事前準備・設計メモ・評価データの解説）
```

> データの会社名・サービス名は架空です。ディープリサーチの結果の内容は、実在の企業の公開情報をもとに、特定できないよう加工しています。
