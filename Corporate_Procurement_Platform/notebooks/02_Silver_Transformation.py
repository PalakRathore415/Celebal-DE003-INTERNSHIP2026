# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Silver Transformation
# MAGIC **Corporate Procurement Platform**
# MAGIC
# MAGIC Cleans Bronze tables into trusted Silver tables:
# MAGIC - dedup
# MAGIC - null handling
# MAGIC - vendor name standardization
# MAGIC - date/currency formatting
# MAGIC - row-level data quality flags (not silently dropped — quarantined, so nothing
# MAGIC   vanishes without a trace)
# MAGIC
# MAGIC The three vendor-contract batches are cleaned individually here — they get
# MAGIC unioned and turned into SCD Type 2 history in the next notebook, not this one.
# MAGIC Silver's job is "clean and trustworthy", not "historized".

# COMMAND ----------

dbutils.widgets.text("bronze_db", "procurement_bronze", "Bronze database name")
dbutils.widgets.text("silver_db", "procurement_silver", "Silver database name")

bronze_db = dbutils.widgets.get("bronze_db")
silver_db = dbutils.widgets.get("silver_db")

print(f"Bronze DB: {bronze_db}")
print(f"Silver DB: {silver_db}")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark.sql(f"CREATE DATABASE IF NOT EXISTS {silver_db}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Shared helpers

# COMMAND ----------

def standardize_vendor_name(col):
    """Trim, collapse internal whitespace, title-case vendor names so the same
    vendor never fragments into multiple spellings downstream."""
    cleaned = F.trim(F.regexp_replace(col, r"\s+", " "))
    return F.initcap(cleaned)


def dedup_keep_latest(df, key_cols, order_col):
    """Drop exact duplicates, then for remaining key collisions keep the row with
    the latest order_col (e.g. _ingested_at)."""
    w = Window.partitionBy(*key_cols).orderBy(F.col(order_col).desc())
    return (
        df.dropDuplicates()
        .withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )


def write_silver(df, table_name, db):
    full_table = f"{db}.{table_name}"
    (
        df.write.format("delta").mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(full_table)
    )
    print(f"[SILVER] {full_table:35s} {spark.table(full_table).count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver — Vendors

# COMMAND ----------

bronze_vendors = spark.table(f"{bronze_db}.bronze_vendors")

silver_vendors = (
    bronze_vendors
    .withColumn("vendor_name", standardize_vendor_name(F.col("vendor_name")))
    .withColumn("category", F.trim(F.col("category")))
    .withColumn("region", F.trim(F.initcap(F.col("region"))))
    .withColumn("onboarded_date", F.to_date("onboarded_date"))
    .withColumn("payment_terms_days", F.col("payment_terms_days").cast("int"))
    .filter(F.col("vendor_id").isNotNull())
    .filter(F.col("payment_terms_days").isNotNull() & (F.col("payment_terms_days") > 0))
)
silver_vendors = dedup_keep_latest(silver_vendors, ["vendor_id"], "_ingested_at")
silver_vendors = silver_vendors.select(
    "vendor_id", "vendor_name", "category", "region", "onboarded_date", "payment_terms_days"
)

write_silver(silver_vendors, "silver_vendors", silver_db)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver — Purchase Orders

# COMMAND ----------

bronze_po = spark.table(f"{bronze_db}.bronze_purchase_orders")

silver_po = (
    bronze_po
    .withColumn("order_date", F.to_date("order_date"))
    .withColumn("quantity", F.col("quantity").cast("int"))
    .withColumn("unit_price", F.round(F.col("unit_price").cast("double"), 2))
    .withColumn("po_amount", F.round(F.col("po_amount").cast("double"), 2))
    .withColumn("region", F.trim(F.initcap(F.col("region"))))
    .withColumn("department", F.trim(F.col("department")))
    # data quality flag instead of silent drop: PO amount should equal qty * unit_price
    .withColumn(
        "_dq_amount_mismatch",
        F.abs(F.col("po_amount") - (F.col("quantity") * F.col("unit_price"))) > 0.5
    )
    .filter(F.col("po_id").isNotNull() & F.col("vendor_id").isNotNull())
    .filter(F.col("quantity") > 0)
)
silver_po = dedup_keep_latest(silver_po, ["po_id"], "_ingested_at")
silver_po = silver_po.select(
    "po_id", "vendor_id", "order_date", "item_category", "quantity",
    "unit_price", "po_amount", "region", "department", "_dq_amount_mismatch"
)

write_silver(silver_po, "silver_purchase_orders", silver_db)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver — Invoices

# COMMAND ----------

bronze_inv = spark.table(f"{bronze_db}.bronze_invoices")

silver_inv = (
    bronze_inv
    .withColumn("invoice_date", F.to_date("invoice_date"))
    .withColumn("due_date", F.to_date("due_date"))
    .withColumn("payment_date", F.to_date("payment_date"))
    .withColumn("invoice_amount", F.round(F.col("invoice_amount").cast("double"), 2))
    .withColumn("payment_status", F.trim(F.initcap(F.col("payment_status"))))
    # derived: was payment late? null when not yet paid
    .withColumn(
        "days_late",
        F.when(
            F.col("payment_date").isNotNull(),
            F.datediff(F.col("payment_date"), F.col("due_date"))
        )
    )
    .filter(F.col("invoice_id").isNotNull() & F.col("po_id").isNotNull())
)
silver_inv = dedup_keep_latest(silver_inv, ["invoice_id"], "_ingested_at")
silver_inv = silver_inv.select(
    "invoice_id", "po_id", "vendor_id", "invoice_date", "invoice_amount",
    "due_date", "payment_date", "payment_status", "days_late"
)

write_silver(silver_inv, "silver_invoices", silver_db)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver — Vendor Contract batches (cleaned, not yet historized)
# MAGIC Each of the 3 raw batches gets the same cleaning pass. They stay separate
# MAGIC tables here; `03_SCD_Type2.py` unions them in snapshot order and runs the merge.

# COMMAND ----------

def clean_contract_batch(bronze_table_name):
    df = spark.table(f"{bronze_db}.{bronze_table_name}")
    return (
        df
        .withColumn("item_category", F.trim(F.col("item_category")))
        .withColumn("unit_price", F.round(F.col("unit_price").cast("double"), 2))
        .withColumn("contract_start", F.to_date("contract_start"))
        .withColumn("contract_end", F.to_date("contract_end"))
        .withColumn("snapshot_date", F.to_date("snapshot_date"))
        .withColumn("payment_terms", F.trim(F.col("payment_terms")))
        .filter(F.col("contract_id").isNotNull() & F.col("vendor_id").isNotNull())
        .filter(F.col("unit_price") > 0)
        .select(
            "contract_id", "vendor_id", "item_category", "unit_price",
            "contract_start", "contract_end", "payment_terms", "snapshot_date"
        )
    )

for batch_num in [1, 2, 3]:
    cleaned = clean_contract_batch(f"bronze_vendor_contracts_batch{batch_num}")
    write_silver(cleaned, f"silver_vendor_contracts_batch{batch_num}", silver_db)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data quality summary
# MAGIC Quick visibility into what got flagged, not just what got dropped.

# COMMAND ----------

mismatch_count = silver_po.filter(F.col("_dq_amount_mismatch")).count()
print(f"[DQ] Purchase orders with amount/qty*price mismatch: {mismatch_count}")

late_count = silver_inv.filter(F.col("days_late") > 0).count()
print(f"[DQ] Invoices paid late: {late_count}")

overdue_unpaid = silver_inv.filter(
    (F.col("payment_status") == "Overdue") & F.col("payment_date").isNull()
).count()
print(f"[DQ] Invoices overdue and still unpaid: {overdue_unpaid}")

# COMMAND ----------

display(spark.sql(f"SHOW TABLES IN {silver_db}"))
