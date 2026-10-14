# Databricks notebook source
# MAGIC %md
# MAGIC # Step 0 設定の確認
# MAGIC 自分用のスキーマ名・エンドポイント名などを表示し、スキーマを作ります。

# COMMAND ----------

# MAGIC %run ../_config

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FQ}")
print("スキーマを用意しました:", FQ)
