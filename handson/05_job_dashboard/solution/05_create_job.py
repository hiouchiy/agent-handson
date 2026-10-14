# Databricks notebook source
# MAGIC %md
# MAGIC # Step 5 ジョブを作る（模範解答）
# MAGIC UI（**ジョブとパイプライン** → **作成** → **ジョブ**）で作るのと同じものを、コードで作ります。
# MAGIC
# MAGIC | タスク | ノートブック | 依存 |
# MAGIC |---|---|---|
# MAGIC | `extract_characteristics` | `task1_extract_characteristics` | — |
# MAGIC | `score` | `task2_score` | `extract_characteristics` |
# MAGIC | `write_results` | `task3_write_results` | `score` |
# MAGIC
# MAGIC 計算資源はサーバーレス。スケジュールは毎朝 6 時（日本時間）で、作成時は一時停止にしておきます。

# COMMAND ----------

# MAGIC %run ../../_config

# COMMAND ----------

import os

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

w = WorkspaceClient()
here = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())


def task(key, notebook, depends_on=None):
    return jobs.Task(task_key=key, notebook_task=jobs.NotebookTask(notebook_path=f"{here}/{notebook}"),
                     depends_on=[jobs.TaskDependency(task_key=depends_on)] if depends_on else None,
                     environment_key="default")


job = w.jobs.create(
    name=f"見込み顧客スコアリング（{PARTICIPANT}）",
    tasks=[task("extract_characteristics", "task1_extract_characteristics"),
           task("score", "task2_score", "extract_characteristics"),
           task("write_results", "task3_write_results", "score")],
    environments=[jobs.JobEnvironment(environment_key="default", spec=jobs.compute.Environment(client="4"))],
    schedule=jobs.CronSchedule(quartz_cron_expression="0 0 6 * * ?", timezone_id="Asia/Tokyo",
                               pause_status=jobs.PauseStatus.PAUSED),
    max_concurrent_runs=1,
)
print("ジョブを作成しました:", job.job_id)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 実行する
# MAGIC ジョブの画面で **今すぐ実行** を押すか、次のセルを実行します（3 社で 3〜5 分ほど）。

# COMMAND ----------

run = w.jobs.run_now(job_id=job.job_id).result()
print(run.state.result_state, run.run_page_url)
display(spark.table(f"{FQ}.customer_product_score"))
