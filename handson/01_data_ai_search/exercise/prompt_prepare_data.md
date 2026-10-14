# Omnigent に送るプロンプト（Step 1 データの準備）

```
handson/01_data_ai_search/README.md の「用意するデータ」のうち、自分のスキーマに作るもの
（crm_account テーブル・research Volume・Managed Agent Memory）を作る Databricks ノートブックを、
handson/my_work/01_prepare_data.py として作ってください。過去の受注事例のテーブルとインデックスは、
代表者が共有スキーマに作ったものを使うので、作らないでください。

条件:
- ノートブック（ソース形式）にする。先頭で %run ../_config を実行し、_config.py の変数（CATALOG・SCHEMA・FQ・
  CRM_TABLE・RESEARCH_VOLUME・MEMORY_STORE）を使う。名前を直接書かない。
- 自分のスキーマ（FQ）がなければ作る。
- data/crm_accounts.json から crm_account テーブルを作る。
- Volume research を作り、data/research/<会社ID>/research.md を同じフォルダ構成でコピーする。
- Managed Agent Memory（Unity Catalog の Memory Store）を、FQ の中に agent_memory という名前で作る
  （REST API: POST /api/2.1/unity-catalog/memory-stores、body に name・catalog_name・schema_name）。
  すでにあれば作らない。
- Memory の scope "shared" に、path "/memories/semantic/scoring_rules.md" で採点の共通ルールを入れる
  （POST /api/2.1/unity-catalog/memory-stores/<store>/entries?scope=shared、body に path・contents・description）。
  ルールの中身は「重要インフラ・古いシステム・人材不足・規制業種・直近のインシデントの会社ほど見込みが高い。
  クラウドネイティブで修正の対象が小さい会社や、競合が入っていて提案の余地がない会社は低い」という趣旨で書く。
  すでに入っていれば入れない。
- REST API は databricks-sdk の WorkspaceClient().api_client.do(...) で呼ぶ。
- 最後のセルで、共有のインデックス（_config.py の CASE_INDEX）に「病院 電子カルテ 人手不足」で検索し、
  自分から検索できることを確かめる。
- 各セルの最後に、作ったものを display か print で確認できるようにする。セルの説明は日本語の Markdown セルで書く。

できたら、ワークスペースの handson/my_work/ に反映してください。
```
