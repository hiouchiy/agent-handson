#!/bin/bash
# ワークスペースのノートブックを、サーバーレスのジョブとして実行し、終わるまで待って結果を表示する。
#
#   bash handson/tools/run_notebook.sh <ワークスペースのノートブックのパス> ['<パラメータの JSON>']
#
# 例:
#   bash handson/tools/run_notebook.sh /Workspace/Users/taro@example.com/agent-handson-main/handson/my_work/01_prepare_data
#   bash handson/tools/run_notebook.sh /Workspace/Users/.../03_evaluate '{"agent_dir": "../my_work"}'
#
# 表示するもの: 結果（SUCCESS / FAILED）、実行の画面の URL、セルの出力、失敗したときのエラー。
set -u
NOTEBOOK="${1:?ワークスペースのノートブックのパスを指定してください}"
PARAMS="${2:-}"
[ -z "$PARAMS" ] && PARAMS="{}"
WORK="$(mktemp -d)"

python3 - "$NOTEBOOK" "$PARAMS" > "$WORK/submit.json" <<'PY'
import json, sys
notebook, params = sys.argv[1], json.loads(sys.argv[2])
print(json.dumps({
    "run_name": "handson: " + notebook.rsplit("/", 1)[-1],
    "tasks": [{"task_key": "notebook", "environment_key": "default",
               "notebook_task": {"notebook_path": notebook, "source": "WORKSPACE", "base_parameters": params}}],
    "environments": [{"environment_key": "default", "spec": {"client": "4"}}],
}))
PY

RUN_ID=$(databricks jobs submit --no-wait --json @"$WORK/submit.json" -o json | python3 -c "import json,sys; print(json.load(sys.stdin)['run_id'])") || {
  echo "ジョブを投入できませんでした"; exit 1; }
echo "実行を始めました（run_id: ${RUN_ID}）。終わるまで待ちます..."

# 終わるまで待つ（通信が一時的に切れても、待ち直す）
while true; do
  STATE=$(databricks jobs get-run "$RUN_ID" -o json 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d['state']['life_cycle_state'], d['state'].get('result_state') or '-', d.get('run_page_url') or '-', d['tasks'][-1]['run_id'])" 2>/dev/null)
  case "$STATE" in TERMINATED*|INTERNAL_ERROR*|SKIPPED*) break ;; esac
  sleep 20
done
read -r LIFE RESULT URL TASK_RUN_ID <<< "$STATE"
[ "$RESULT" = "-" ] && RESULT="$LIFE"
echo "結果: ${RESULT}"
echo "実行の画面: ${URL}"

# セルの出力（実行したノートブックを書き出して、出力を取り出す）
databricks jobs export-run "$TASK_RUN_ID" --views-to-export CODE -o json > "$WORK/export.json" 2>/dev/null && python3 - "$WORK/export.json" <<'PY'
import base64, json, re, sys, urllib.parse
views = json.load(open(sys.argv[1])).get("views", [])
for v in views:
    m = re.search(r"__DATABRICKS_NOTEBOOK_MODEL = '([^']+)'", v.get("content", ""))
    if not m:
        continue
    model = json.loads(urllib.parse.unquote(base64.b64decode(m.group(1)).decode()))
    for cmd in model.get("commands", []):
        r = cmd.get("results") or {}
        data = r.get("data")
        text = ""
        if isinstance(data, str):
            text = data
        elif isinstance(data, list):
            text = "\n".join(x.get("data", "") for x in data if isinstance(x, dict) and isinstance(x.get("data"), str))
        if text.strip():
            print("--- セルの出力:", (cmd.get("command") or "").strip().splitlines()[0][:60] if cmd.get("command") else "")
            print(text.strip()[-2000:])
PY

# 失敗したときのエラー
if [ "$RESULT" != "SUCCESS" ]; then
  databricks jobs get-run-output "$TASK_RUN_ID" -o json 2>/dev/null | python3 -c "
import json, re, sys
d = json.load(sys.stdin)
print('エラー:', d.get('error'))
print(re.sub(r'\x1b\[[0-9;]*m', '', d.get('error_trace') or '')[-3000:])"
  exit 1
fi
