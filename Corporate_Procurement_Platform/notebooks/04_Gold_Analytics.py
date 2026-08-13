# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Gold Analytics
# MAGIC **Corporate Procurement Platform**
# MAGIC
# MAGIC Builds the business-facing Gold tables from Silver + the SCD2 contract history:
# MAGIC 1. Total vendor spend
# MAGIC 2. Invoice vs. contract price variance
# MAGIC 3. Vendor risk classification
# MAGIC 4. Region-wise spend
# MAGIC 5. Monthly procurement trend
# MAGIC
# MAGIC Every table here answers a specific question a procurement manager would
# MAGIC actually ask — that framing (not just "aggregate the data") is what should
# MAGIC come through in the Power BI pages later.

# COMMAND ----------

dbutils.widgets.text("silver_db", "procurement_silver", "Silver database name")
dbutils.widgets.text("gold_db", "procurement_gold", "Gold database name")

silver_db = dbutils.widgets.get("silver_db")
gold_db = dbutils.widgets.get("gold_db")

spark.sql(f"CREATE DATABASE IF NOT EXISTS {gold_db}")
print(f"Silver DB: {silver_db}")
print(f"Gold DB  : {gold_db}")

# COMMAND ----------

from pyspark.sql import functions as F

vendors = spark.table(f"{silver_db}.silver_vendors")
pos = spark.table(f"{silver_db}.silver_purchase_orders")
invoices = spark.table(f"{silver_db}.silver_invoices")
contracts_current = spark.table(f"{silver_db}.silver_vendor_contracts_scd2").filter("is_current = true")

def write_gold(df, table_name):
    full_table = f"{gold_db}.{table_name}"
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(full_table)
    print(f"[GOLD] {full_table:35s} {spark.table(full_table).count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Total Vendor Spend
# MAGIC Total PO value and invoiced value per vendor, plus PO count — the baseline
# MAGIC "who are we spending the most with" table.

# COMMAND ----------

gold_vendor_spend = (
    pos.groupBy("vendor_id")
    .agg(
        F.sum("po_amount").alias("total_po_amount"),
        F.count("po_id").alias("po_count"),
        F.round(F.avg("po_amount"), 2).alias("avg_po_amount"),
    )
    .join(
        invoices.groupBy("vendor_id").agg(F.sum("invoice_amount").alias("total_invoiced_amount")),
        on="vendor_id", how="left"
    )
    .join(vendors.select("vendor_id", "vendor_name", "category", "region"), on="vendor_id", how="left")
    .withColumn("total_invoiced_amount", F.coalesce(F.col("total_invoiced_amount"), F.lit(0.0)))
    .select(
        "vendor_id", "vendor_name", "category", "region",
        "po_count", "total_po_amount", "avg_po_amount", "total_invoiced_amount"
    )
    .orderBy(F.desc("total_po_amount"))
)

write_gold(gold_vendor_spend, "gold_vendor_spend")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Invoice vs. Contract Price Variance
# MAGIC For every PO, compares the price actually invoiced (per unit) against the
# MAGIC vendor's *current* contract price. Flags where finance is overpaying or
# MAGIC a vendor is underbilling relative to what was negotiated.

# COMMAND ----------

po_with_invoice = (
    pos.alias("po")
    .join(
        invoices.select("po_id", "invoice_amount", "invoice_date").alias("inv"),
        on="po_id", how="inner"
    )
    .join(
        contracts_current.select(
            F.col("vendor_id").alias("c_vendor_id"),
            F.col("unit_price").alias("contract_unit_price")
        ),
        F.col("po.vendor_id") == F.col("c_vendor_id"),
        how="left"
    )
)

gold_invoice_variance = (
    po_with_invoice
    .withColumn("invoiced_unit_price", F.round(F.col("invoice_amount") / F.col("quantity"), 2))
    .withColumn(
        "variance_pct",
        F.when(
            F.col("contract_unit_price").isNotNull() & (F.col("contract_unit_price") > 0),
            F.round(
                (F.col("invoiced_unit_price") - F.col("contract_unit_price"))
                / F.col("contract_unit_price") * 100, 2
            )
        )
    )
    .select(
        "po_id", "vendor_id", "item_category", "quantity",
        "contract_unit_price", "invoiced_unit_price", "invoice_amount", "variance_pct"
    )
    .orderBy(F.desc(F.abs(F.col("variance_pct"))))
)

write_gold(gold_invoice_variance, "gold_invoice_variance")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Vendor Risk Classification
# MAGIC Composite risk score from 4 signals, each worth points, bucketed into
# MAGIC Low / Medium / High. Weights are a starting point — documented here so
# MAGIC they're easy to defend or tune in the README rather than "magic numbers".
# MAGIC
# MAGIC | Signal | Trigger | Points |
# MAGIC |---|---|---|
# MAGIC | Late payments | share of invoices paid late > 20% | 30 |
# MAGIC | Invoice variance | avg abs variance_pct > 10% | 25 |
# MAGIC | Expired contract | current contract `valid_to`/`contract_end` in the past | 25 |
# MAGIC | High spend | vendor in top quartile of total_po_amount | 20 |

# COMMAND ----------

# late payment rate per vendor
late_rate = (
    invoices.withColumn("is_late", (F.col("days_late") > 0).cast("int"))
    .groupBy("vendor_id")
    .agg(
        F.avg("is_late").alias("late_payment_rate"),
        F.count("invoice_id").alias("invoice_count"),
    )
)

# average absolute invoice variance per vendor
variance_by_vendor = (
    gold_invoice_variance
    .filter(F.col("variance_pct").isNotNull())
    .groupBy("vendor_id")
    .agg(F.avg(F.abs(F.col("variance_pct"))).alias("avg_abs_variance_pct"))
)

# contract expiry: current SCD2 row's original contract_end pulled from batch3 (latest snapshot)
latest_contract_end = (
    spark.table(f"{silver_db}.silver_vendor_contracts_batch3")
    .select("vendor_id", "contract_end")
)

# high spend threshold = top quartile cutoff of total_po_amount
spend_threshold = (
    gold_vendor_spend.approxQuantile("total_po_amount", [0.75], 0.01)[0]
)

risk_base = (
    vendors.select("vendor_id", "vendor_name", "category", "region")
    .join(late_rate, on="vendor_id", how="left")
    .join(variance_by_vendor, on="vendor_id", how="left")
    .join(latest_contract_end, on="vendor_id", how="left")
    .join(gold_vendor_spend.select("vendor_id", "total_po_amount"), on="vendor_id", how="left")
)

gold_vendor_risk = (
    risk_base
    .withColumn("late_payment_rate", F.coalesce(F.col("late_payment_rate"), F.lit(0.0)))
    .withColumn("avg_abs_variance_pct", F.coalesce(F.col("avg_abs_variance_pct"), F.lit(0.0)))
    .withColumn("contract_expired", F.col("contract_end") < F.current_date())
    .withColumn(
        "risk_score",
        (F.when(F.col("late_payment_rate") > 0.20, 30).otherwise(0))
        + (F.when(F.col("avg_abs_variance_pct") > 10, 25).otherwise(0))
        + (F.when(F.col("contract_expired"), 25).otherwise(0))
        + (F.when(F.col("total_po_amount") >= F.lit(spend_threshold), 20).otherwise(0))
    )
    .withColumn(
        "risk_category",
        F.when(F.col("risk_score") >= 55, "High")
        .when(F.col("risk_score") >= 25, "Medium")
        .otherwise("Low")
    )
    .select(
        "vendor_id", "vendor_name", "category", "region",
        F.round("late_payment_rate", 3).alias("late_payment_rate"),
        F.round("avg_abs_variance_pct", 2).alias("avg_abs_variance_pct"),
        "contract_expired", "risk_score", "risk_category"
    )
    .orderBy(F.desc("risk_score"))
)

write_gold(gold_vendor_risk, "gold_vendor_risk")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Region-Wise Spend

# COMMAND ----------

gold_region_spend = (
    pos.groupBy("region")
    .agg(
        F.sum("po_amount").alias("total_spend"),
        F.count("po_id").alias("po_count"),
        F.countDistinct("vendor_id").alias("vendor_count"),
    )
    .orderBy(F.desc("total_spend"))
)

write_gold(gold_region_spend, "gold_region_spend")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Monthly Procurement Trend

# COMMAND ----------

monthly_po = (
    pos.withColumn("month", F.date_trunc("month", "order_date"))
    .groupBy("month")
    .agg(F.sum("po_amount").alias("total_po_spend"), F.count("po_id").alias("po_count"))
)

monthly_inv = (
    invoices.withColumn("month", F.date_trunc("month", "invoice_date"))
    .groupBy("month")
    .agg(F.count("invoice_id").alias("invoice_count"))
)

gold_monthly_trend = (
    monthly_po.join(monthly_inv, on="month", how="left")
    .withColumn("invoice_count", F.coalesce(F.col("invoice_count"), F.lit(0)))
    .orderBy("month")
)

write_gold(gold_monthly_trend, "gold_monthly_trend")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("[GOLD] Risk category breakdown:")
display(gold_vendor_risk.groupBy("risk_category").count().orderBy(F.desc("count")))

print("[GOLD] Top 5 vendors by spend:")
display(gold_vendor_spend.limit(5))
