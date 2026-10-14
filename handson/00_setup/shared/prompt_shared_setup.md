# Omnigent に送るプロンプト（Step 0 共有の準備・代表者だけ）

代表者 1 名が、自分の Omnigent に送ります。ほかの参加者は、この間にエージェントスキルを入れておきます。
うまくいかないときは、[00_shared_setup](00_shared_setup.py) ノートブックをそのまま実行して作ります（同じものができます）。

```
ハンズオンの参加者全員で使う、過去の受注事例の AI Search（旧 Vector Search）を用意してください。
設定値は handson/settings.json の値から handson/_config.py の決め方で求めたもの（CATALOG・SHARED_FQ・CASE_TABLE・CASE_INDEX・AI_SEARCH_ENDPOINT・EMBEDDING_ENDPOINT）を
使ってください。Databricks のスキル（databricks-vector-search、databricks-unity-catalog）を参照して進めてください。

やること:
1. 共有スキーマ SHARED_FQ を作る（なければ）。
2. handson/data/reference_cases.json（case_id・industry・title・content の 10 件）から、Delta テーブル CASE_TABLE を作り、
   Change Data Feed を有効にする。
3. AI Search のエンドポイント AI_SEARCH_ENDPOINT（Standard）を作る（すでにあれば作らない）。
4. CASE_TABLE を元に、Delta Sync のインデックス CASE_INDEX を作る。主キーは case_id、埋め込みを計算する列は content、
   埋め込みモデルは EMBEDDING_ENDPOINT、同期はトリガー。最初の同期が終わるまで待つ（10 分ほどかかることがある）。
   状態の ready はインデックスができた時点で true になるので、取り込んだ行数（indexed_row_count）が
   元のテーブルの件数と同じになるまで待つ。
5. 参加者全員が読めて、検索できるように権限を付ける。
   - Unity Catalog: カタログ CATALOG に USE CATALOG、スキーマ SHARED_FQ に USE SCHEMA と SELECT を、`account users` に付ける。
   - AI Search のエンドポイント: ワークスペースのグループ `users` に CAN_USE を付ける。
6. 「病院 電子カルテ 人手不足」で検索して、RC03 が一番上に来ることを確かめる。
7. 作ったもの・付けた権限・検索の結果を表で報告する。
```
