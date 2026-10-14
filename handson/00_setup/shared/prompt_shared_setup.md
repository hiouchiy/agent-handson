# Omnigent に送るプロンプト（Step 0 共有の準備・代表者だけ）

代表者 1 名が、自分の Omnigent に送ります。ほかの参加者は、この間に手順 5 までを済ませておきます。
うまくいかないときは、[00_shared_setup](00_shared_setup.py) ノートブックを実行して作ります（同じものができます）。

**このプロンプトで頼んでいること**: 参加者全員で使う、過去の受注事例の AI Search（エンドポイントとインデックス）を作り、全員が使えるように権限を付けてもらう。

```
## やりたいこと
参加者全員で使う、過去の受注事例の AI Search（旧 Vector Search）を用意してください。

## 作るもの
1. 共有スキーマ（なければ）
2. data/reference_cases.json（10 件）から、事例のテーブル reference_case（Change Data Feed を有効にする）
3. AI Search のエンドポイント（Standard。すでにあれば作らない）
4. 事例のテーブルを元にした、Delta Sync のインデックス（主キー case_id、埋め込みを計算する列 content、同期はトリガー）
5. 全員が読めて検索できる権限
   - Unity Catalog: カタログに USE CATALOG、共有スキーマに USE SCHEMA と SELECT（`account users` に）
   - AI Search のエンドポイント: CAN_USE（ワークスペースのグループ `users` に）

## 決まりごと
- 名前（カタログ・共有スキーマ・テーブル・インデックス・エンドポイント・埋め込みモデル）は、
  handson/settings.json から handson/_config.py の決め方で求める
- Databricks のスキル（databricks-vector-search、databricks-unity-catalog）を参考に進める

## 気をつけること
- インデックスの状態の ready は、インデックスができた時点で true になる。取り込んだ行数（indexed_row_count）が
  元のテーブルの件数と同じになるまで待つ（作成直後のエンドポイントでは 10 分ほどかかる）

## 参考にするもの
- 同じことをするノートブック: handson/00_setup/shared/00_shared_setup.py

## できたら
「病院 電子カルテ 人手不足」で検索して、RC03 が一番上に来ることを確かめてください。
作ったもの・付けた権限・検索の結果を表にして報告してください。
```
