# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — SCD Type 2 on Vendor Contracts
# MAGIC **Corporate Procurement Platform**
# MAGIC
# MAGIC The centerpiece of the pipeline. Processes the 3 cleaned contract snapshots
# MAGIC (`silver_vendor_contracts_batch1/2/3`) **in snapshot order**, one Delta `MERGE`
# MAGIC per batch, to build a full Type 2 history table:
# MAGIC
# MAGIC | vendor_id | unit_price | valid_from | valid_to   | is_current |
# MAGIC |-----------|-----------|------------|------------|------------|
# MAGIC | V003      | 479.22    | 2025-01-01 | 2025-07-01 | false      |
# MAGIC | V003      | 598.56    | 2025-07-01 | 9999-12-31 | true       |
# MAGIC
# MAGIC Processing snapshots one at a time (instead of just diffing batch1 vs batch3)
# MAGIC matters: it's what makes this a real incremental SCD2 pattern rather than a
# MAGIC one-off "compare two files" script. In production you'd get a new snapshot
# MAGIC every day/week and re-run this same merge each time.

# COMMAND ----------

dbutils.widgets.text("silver_db", "procurement_silver", "Silver database name")

silver_db = dbutils.widgets.get("silver_db")
target_table = f"{silver_db}.silver_vendor_contracts_scd2"

print(f"Silver DB     : {silver_db}")
print(f"Target table  : {target_table}")

# COMMAND ----------

from pyspark.sql import functions as F
from delta.tables import DeltaTable

FAR_FUTURE_DATE = "9999-12-31"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 — seed the SCD2 table from batch 1
# MAGIC First run, so there's no prior history to merge against — every row starts
# MAGIC as the current version.

# COMMAND ----------

if not spark.catalog.tableExists(target_table):
    batch1 = spark.table(f"{silver_db}.silver_vendor_contracts_batch1")

    seed = (
        batch1
        .withColumnRenamed("contract_start", "valid_from")
        .withColumn("valid_to", F.lit(FAR_FUTURE_DATE).cast("date"))
        .withColumn("is_current", F.lit(True))
        .drop("contract_end", "snapshot_date")
    )

    (
        seed.write.format("delta").mode("overwrite")
        .saveAsTable(target_table)
    )
    print(f"[SCD2] Seeded {target_table} with {seed.count()} rows from batch 1")
else:
    print(f"[SCD2] {target_table} already exists — skipping seed, will merge batches 2+3 below")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 — the merge function
# MAGIC Standard two-step SCD2 pattern via Delta `MERGE`:
# MAGIC
# MAGIC 1. **Close out** existing current rows whose price changed in the new batch
# MAGIC    (`is_current = false`, `valid_to = new batch's snapshot_date`)
# MAGIC 2. **Insert** new current rows for anything new or changed
# MAGIC
# MAGIC Delta doesn't let one `MERGE` both update-and-insert-a-different-row for the
# MAGIC same key in one pass when the update and the insert need different values —
# MAGIC so this is done as an update-only merge followed by an append of new rows,
# MAGIC which is the standard, well-documented way to do SCD2 with Delta `MERGE`.

# COMMAND ----------

def apply_scd2_batch(batch_table: str, batch_num: int):
    print(f"\n[SCD2] Processing {batch_table} (batch {batch_num}) ...")

    new_batch = spark.table(f"{silver_db}.{batch_table}")
    scd2_table = DeltaTable.forName(spark, target_table)
    current_df = scd2_table.toDF().filter("is_current = true")

    # rows whose price (or category/terms) actually changed vs. current version
    changed = (
        new_batch.alias("new")
        .join(current_df.alias("cur"), on="vendor_id", how="inner")
        .filter(
            (F.col("new.unit_price") != F.col("cur.unit_price"))
            | (F.col("new.item_category") != F.col("cur.item_category"))
        )
        .select("new.*")
    )

    # vendors appearing for the first time in this batch (new contracts)
    new_vendors = new_batch.join(current_df, on="vendor_id", how="left_anti")

    to_insert = changed.unionByName(new_vendors)
    insert_count = to_insert.count()

    if insert_count == 0:
        print(f"[SCD2] No price/category changes in batch {batch_num} — nothing to version")
        return 0

    # 1) close out the current rows that are being superseded
    changed_vendor_ids = [r["vendor_id"] for r in changed.select("vendor_id").distinct().collect()]
    if changed_vendor_ids:
        (
            scd2_table.alias("t")
            .merge(
                changed.select("vendor_id").distinct().alias("s"),
                "t.vendor_id = s.vendor_id AND t.is_current = true"
            )
            .whenMatchedUpdate(set={
                "is_current": "false",
                "valid_to": f"'{new_batch.select('snapshot_date').first()[0]}'",
            })
            .execute()
        )
        print(f"[SCD2] Closed out {len(changed_vendor_ids)} superseded current row(s)")

    # 2) insert the new current versions (changed + brand-new vendors)
    to_append = (
        to_insert
        .withColumnRenamed("contract_start", "valid_from")
        .withColumn("valid_to", F.lit(FAR_FUTURE_DATE).cast("date"))
        .withColumn("is_current", F.lit(True))
        .drop("contract_end", "snapshot_date")
    )
    to_append.write.format("delta").mode("append").saveAsTable(target_table)
    print(f"[SCD2] Inserted {insert_count} new current row(s) for batch {batch_num}")

    return insert_count

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 — run batches 2 and 3 through the merge

# COMMAND ----------

for batch_num in [2, 3]:
    apply_scd2_batch(f"silver_vendor_contracts_batch{batch_num}", batch_num)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 — validate the result
# MAGIC Every vendor should have exactly one current row, and history rows should
# MAGIC never overlap in time for the same vendor.

# COMMAND ----------

result = spark.table(target_table)

current_per_vendor = (
    result.filter("is_current = true")
    .groupBy("vendor_id")
    .count()
    .filter("count != 1")
)
bad_current_count = current_per_vendor.count()
print(f"[VALIDATE] Vendors without exactly 1 current row: {bad_current_count}")
if bad_current_count > 0:
    display(current_per_vendor)

total_rows = result.count()
vendors_with_history = (
    result.groupBy("vendor_id").count().filter("count > 1").count()
)
print(f"[VALIDATE] Total SCD2 rows: {total_rows}")
print(f"[VALIDATE] Vendors with 2+ historical versions: {vendors_with_history}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preview — a vendor with price history

# COMMAND ----------

sample_vendor = (
    result.groupBy("vendor_id").count().filter("count > 1")
    .orderBy(F.desc("count")).first()
)
if sample_vendor:
    display(
        result.filter(F.col("vendor_id") == sample_vendor["vendor_id"])
        .orderBy("valid_from")
    )

# COMMAND ----------

display(result.orderBy("vendor_id", "valid_from"))
