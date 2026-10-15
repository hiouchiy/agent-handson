"""rubric.py の業務の決めごと（観点・段階・点数の範囲・共通ルール・補正・Tier）を、業務の人が読む Markdown の表にする。

    python3 handson/tools/make_rubric_doc.py <rubric.py があるフォルダ> <書き出す Markdown のパス>

例: python3 handson/tools/make_rubric_doc.py handson/02_agent/solution handson/02_agent/rubric.md
"""
import importlib.util
import os
import sys

src_dir, out = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("rubric", os.path.join(src_dir, "rubric.py"))
rubric = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rubric)

lines = [
    f"# 採点基準（版 {rubric.RUBRIC_VERSION}）",
    "",
    "見込み顧客を 5 つの観点（合計 100 点）と関係性の補正で採点します。",
    "エージェントの LLM は、観点ごとに「段階を選び、その段階の点数の範囲で点数を付け、根拠を書く」だけを行います。"
    "合計・Tier・確からしさは、プログラムが計算します。",
    "",
    f"> この表は `{os.path.relpath(os.path.join(src_dir, 'rubric.py'), os.path.dirname(os.path.abspath(out)) or '.')}` から"
    " `tools/make_rubric_doc.py` で作ったものです。本番では、業務部門がこのような採点基準を Excel などのドキュメントで持ち、"
    "エージェントがそれを読み込みます。ハンズオンでは時間の都合で、それを書き写した `rubric.py` を使います。",
    "",
    "## Tier の区切り",
    "",
    f"| Tier | 合計点 |",
    "|---|---|",
    f"| A | {rubric.TIER_A_MIN} 点以上 |",
    f"| B | {rubric.TIER_B_MIN}〜{rubric.TIER_A_MIN - 1} 点 |",
    f"| C | {rubric.TIER_B_MIN} 点未満 |",
    "",
    "## 5 つの観点",
    "",
]
for key, name, max_points, materials, levels, note in rubric.AXES:
    lines += [f"### {name}（満点 {max_points} 点）", "", f"主な判断材料: {materials}", "",
              "| 段階 | 点数の範囲 | 状態 |", "|---|---|---|"]
    lines += [f"| {lv} | {lo}〜{hi} 点 | {state} |" for lv, lo, hi, state in levels]
    lines += ["", f"補足: {note}", ""]
lines += [f"## 関係性の補正（{rubric.ADJUSTMENT_MIN}〜{rubric.ADJUSTMENT_MAX} 点）", "",
          "| 段階 | 補正 | 状態 |", "|---|---|---|"]
lines += [f"| {lv} | {lo}〜{hi} 点 | {state} |" if lo != hi else f"| {lv} | {lo} 点 | {state} |"
          for lv, lo, hi, state in rubric.ADJUSTMENT_LEVELS]
lines += ["", f"補足: {rubric.ADJUSTMENT_NOTE}", "", rubric.COMMON_RULES.replace("# 共通ルール", "## 共通ルール\n"), ""]

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("書き出しました:", out)
