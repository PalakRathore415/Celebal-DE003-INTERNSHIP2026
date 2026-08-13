# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Bronze Ingestion
# MAGIC **Corporate Procurement Platform**
# MAGIC
# MAGIC Reads raw CSVs (Vendors, Purchase Orders, Invoices, Vendor Contract snapshots)
# MAGIC and lands them as Delta tables in the `procurement_bronze` schema.
# MAGIC
# MAGIC No business-logic transformations happen here — only:
# MAGIC - schema application on read
# MAGIC - ingestion metadata columns (`_source_file`, `_ingested_at`)
# MAGIC - row-count validation logging
# MAGIC
# MAGIC Parameterized via widgets so this notebook can be rerun against any upload path
# MAGIC without editing code.

# COMMAND ----------

dbutils.widgets.text("raw_base_path", "/FileStore/tables/procurement/", "Raw CSV base path")
dbutils.widgets.text("bronze_db", "procurement_bronze", "Bronze database name")

raw_base_path = dbutils.widgets.get("raw_base_path")
bronze_db = dbutils.widgets.get("bronze_db")

print(f"Raw base path : {raw_base_path}")
print(f"Bronze DB     : {bronze_db}")

# COMMAND ----------

from pyspark.sql import functions as F

spark.sql(f"CREATE DATABASE IF NOT EXISTS {bronze_db}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingestion config
# MAGIC One entry per source file. Keeping this as a list of dicts (instead of copy-pasted
# MAGIC read/write blocks per file) is what makes the notebook reusable — add a new source
# MAGIC by adding one line here, not by duplicating 15 lines of Spark code.

# COMMAND ----------

INGESTION_SOURCES = [
    {"file": "vendors.csv", "table": "bronze_vendors"},
    {"file": "purchase_orders.csv", "table": "bronze_purchase_orders"},
    {"file": "invoices.csv", "table": "bronze_invoices"},
    {"file": "vendor_contracts_batch1.csv", "table": "bronze_vendor_contracts_batch1"},
    {"file": "vendor_contracts_batch2.csv", "table": "bronze_vendor_contracts_batch2"},
    {"file": "vendor_contracts_batch3.csv", "table": "bronze_vendor_contracts_batch3"},
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingestion function + logging
# MAGIC Every load prints a timestamped log line and validates the row count landed
# MAGIC matches what was read — a basic but real data-quality gate, not just a happy-path read.

# COMMAND ----------

def ingest_csv_to_bronze(file_name: str, table_name: str, base_path: str, db: str):
    src_path = base_path.rstrip("/") + "/" + file_name
    log_ts = F.current_timestamp()

    print(f"[BRONZE] Reading {src_path} ...")
    df_raw = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(src_path)
    )
    raw_count = df_raw.count()

    df_bronze = (
        df_raw
        .withColumn("_source_file", F.lit(file_name))
        .withColumn("_ingested_at", log_ts)
    )

    full_table = f"{db}.{table_name}"
    (
        df_bronze.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(full_table)
    )

    written_count = spark.table(full_table).count()

    status = "OK" if written_count == raw_count else "ROW COUNT MISMATCH"
    print(f"[BRONZE] {full_table:45s} raw={raw_count:>5} written={written_count:>5}  [{status}]")

    if status != "OK":
        raise ValueError(f"Bronze ingestion validation failed for {full_table}: "
                          f"read {raw_count} rows but wrote {written_count}")

    return written_count

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run ingestion

# COMMAND ----------

results = {}
for source in INGESTION_SOURCES:
    count = ingest_csv_to_bronze(
        file_name=source["file"],
        table_name=source["table"],
        base_path=raw_base_path,
        db=bronze_db,
    )
    results[source["table"]] = count

print("\n[BRONZE] Ingestion summary")
for table, count in results.items():
    print(f"  {table:45s} {count} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sanity check — list bronze tables

# COMMAND ----------

display(spark.sql(f"SHOW TABLES IN {bronze_db}"))
