"""
Assignment 06 — Spark Architecture & Efficient Data Processing
================================================================
Celebal Technologies | Data Engineer Internship | Week 6

Objective
---------
Understand Spark's architecture (Driver, Cluster Manager, Executors),
Lazy Evaluation / DAG, and build an efficient read -> transform ->
filter -> write pipeline over the Superstore dataset, comparing
CSV vs Parquet along the way.

Run:
    python spark_architecture_pipeline.py

This script is organised as numbered STEPs so it mirrors the notebook
cells 1:1 -- copy any STEP block straight into a notebook cell.
"""

import time
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType
)

DATA_DIR = "../data"
OUT_DIR = "../outputs"


# ---------------------------------------------------------------------------
# STEP 1 — SparkSession = entry point to the Driver
# ---------------------------------------------------------------------------
# Creating a SparkSession starts the DRIVER process for this application.
# The Driver builds the logical plan (DAG), talks to the CLUSTER MANAGER
# to request resources, and schedules tasks onto EXECUTORS.
# master("local[*]") runs Driver + Executors in this one JVM using all
# available cores -- fine for dev/learning, not how a real cluster works
# (there you'd point master at "yarn", "spark://host:7077", or "k8s://...").
spark = (
    SparkSession.builder
    .appName("Assignment06_SparkArchitecture")
    .master("local[*]")
    .config("spark.sql.shuffle.partitions", "8")   # small dataset -> fewer shuffle partitions than the 200 default
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

print(f"Spark version : {spark.version}")
print(f"Default parallelism (cores visible to executors): {spark.sparkContext.defaultParallelism}")


# ---------------------------------------------------------------------------
# STEP 2 — Read CSV WITH AN EXPLICIT SCHEMA (best practice, not inferSchema)
# ---------------------------------------------------------------------------
# inferSchema=True forces Spark to do an extra full (or sampled) pass over
# the file just to guess types -- doubles the read cost on large files.
# Defining the schema up front means ONE pass, correct types every time,
# and no silent surprises (e.g. Postal Code being read as a double).
superstore_schema = StructType([
    StructField("Row ID",        IntegerType(), True),
    StructField("Order ID",      StringType(),  True),
    StructField("Order Date",    StringType(),  True),   # parsed to date in STEP 5
    StructField("Ship Date",     StringType(),  True),
    StructField("Ship Mode",     StringType(),  True),
    StructField("Customer ID",   StringType(),  True),
    StructField("Customer Name", StringType(),  True),
    StructField("Segment",       StringType(),  True),
    StructField("Country",       StringType(),  True),
    StructField("City",          StringType(),  True),
    StructField("State",         StringType(),  True),
    StructField("Postal Code",   StringType(),  True),   # has leading-zero ZIPs -> keep as string
    StructField("Region",        StringType(),  True),
    StructField("Product ID",    StringType(),  True),
    StructField("Category",      StringType(),  True),
    StructField("Sub-Category",  StringType(),  True),
    StructField("Product Name",  StringType(),  True),
    StructField("Sales",         DoubleType(),  True),
    StructField("Quantity",      IntegerType(), True),
    StructField("Discount",      DoubleType(),  True),
    StructField("Profit",        DoubleType(),  True),
])

df_raw = (
    spark.read
    .option("header", "true")
    .option("encoding", "ISO-8859-1")   # this Superstore export isn't UTF-8 (City/State have odd bytes)
    .schema(superstore_schema)
    .csv(f"{DATA_DIR}/Sample - Superstore.csv")
)

print("\n--- Raw schema (explicit, no inferSchema pass) ---")
df_raw.printSchema()
print(f"Row count: {df_raw.count()}")   # count() is an ACTION -> first real execution happens here
df_raw.show(5, truncate=30)

# --- Also demonstrate reading the Parquet source (data/sample.parquet) ---
# No schema/encoding options needed: Parquet is self-describing, it carries
# its own schema and column types in the file's footer metadata.
df_from_parquet = spark.read.parquet(f"{DATA_DIR}/sample.parquet")
print(f"\nRows read from data/sample.parquet: {df_from_parquet.count()}")
print("Parquet infers its schema from file metadata (no .schema()/.option('inferSchema') needed):")
df_from_parquet.printSchema()


# ---------------------------------------------------------------------------
# STEP 3 — Select required columns + basic filtering
# ---------------------------------------------------------------------------
df_selected = df_raw.select(
    "Order ID", "Order Date", "Ship Mode", "Customer Name", "Segment",
    "Region", "State", "City", "Category", "Sub-Category",
    "Sales", "Quantity", "Discount", "Profit"
)

# Narrow transformation: filter (Sales, Quantity, Category are single-column
# predicates, so this is executed independently per partition, no shuffle)
df_filtered = df_selected.filter(
    (F.col("Sales") > 0) & (F.col("Quantity") > 0)
)

print(f"\nRows after column selection + basic filter: {df_filtered.count()}")


# ---------------------------------------------------------------------------
# STEP 4 — Handle nulls
# ---------------------------------------------------------------------------
print("\n--- Null counts per column (before cleaning) ---")
df_filtered.select([
    F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df_filtered.columns
]).show()

# dropna on the columns we actually need downstream; this real dataset has
# no nulls, but the step is here because "handle nulls efficiently" was a
# named requirement -- on a dirtier dataset this is where it happens.
df_clean = df_filtered.dropna(subset=["Order ID", "Sales", "Region", "Category"])
print(f"Rows after null handling: {df_clean.count()}")


# ---------------------------------------------------------------------------
# STEP 5 — Modify DataFrame: rename, cast, add a new column
# ---------------------------------------------------------------------------
df_modified = (
    df_clean
    .withColumnRenamed("Sub-Category", "SubCategory")
    .withColumn("Order Date", F.to_date("Order Date", "M/d/yyyy"))   # cast String -> Date
    .withColumn("Discount", F.col("Discount").cast(DoubleType()))     # explicit cast, no-op here but documents intent
    .withColumn(
        "Profit Margin",                                              # new derived column
        F.round(F.col("Profit") / F.col("Sales"), 4)
    )
    .withColumn(
        "Order Year",
        F.year(F.col("Order Date"))
    )
)

print("\n--- Schema after rename / cast / new columns ---")
df_modified.printSchema()
df_modified.select("Order ID", "Order Date", "SubCategory", "Sales", "Profit", "Profit Margin", "Order Year").show(5)


# ---------------------------------------------------------------------------
# STEP 6 — Wide transformation (triggers a SHUFFLE)
# ---------------------------------------------------------------------------
# groupBy + agg is a WIDE transformation: rows with the same key can live on
# any partition, so Spark must shuffle data across the cluster to bring
# matching keys together before aggregating. This is the expensive part of
# the DAG -- it's also why spark.sql.shuffle.partitions was tuned in STEP 1.
region_category_summary = (
    df_modified
    .groupBy("Region", "Category")
    .agg(
        F.round(F.sum("Sales"), 2).alias("Total Sales"),
        F.round(F.sum("Profit"), 2).alias("Total Profit"),
        F.count("Order ID").alias("Order Count"),
    )
    .orderBy(F.col("Total Sales").desc())
)

print("\n--- Region x Category summary (wide transformation -> shuffle) ---")
region_category_summary.show(20, truncate=False)


# ---------------------------------------------------------------------------
# STEP 7 — Lazy evaluation / DAG in action
# ---------------------------------------------------------------------------
# Everything from df_raw down to region_category_summary is a chain of
# TRANSFORMATIONS -- Spark only records the lineage (a DAG of steps), it does
# NOT touch the data yet. Nothing actually ran on the cluster until an
# ACTION (.count(), .show(), .collect(), .write) was called above.
# .explain() prints the plan Catalyst built without executing anything new.
print("\n--- Logical + physical plan (DAG) for the aggregation ---")
region_category_summary.explain(mode="formatted")


# ---------------------------------------------------------------------------
# STEP 8 — Write pipeline output: Parquet (primary) + CSV (for humans)
# ---------------------------------------------------------------------------
t0 = time.time()
(
    df_modified
    .write.mode("overwrite")
    .partitionBy("Region")                 # physically partitions files by Region on disk
    .parquet(f"{OUT_DIR}/processed_parquet")
)
parquet_write_time = time.time() - t0

t0 = time.time()
(
    df_modified
    .coalesce(1)                           # 1 file for a human-readable CSV; avoid this on real big data
    .write.mode("overwrite")
    .option("header", "true")
    .csv(f"{OUT_DIR}/processed_csv")
)
csv_write_time = time.time() - t0

print(f"\nParquet write time: {parquet_write_time:.2f}s")
print(f"CSV write time    : {csv_write_time:.2f}s")


# ---------------------------------------------------------------------------
# STEP 9 — CSV vs Parquet: read-back + predicate pushdown comparison
# ---------------------------------------------------------------------------
# Read the Parquet we just wrote and filter on a column. Because Parquet is
# columnar and stores per-column statistics (min/max) per row-group,
# Spark can push the filter DOWN into the file scan itself -- entire
# row-groups that can't match are skipped without being decompressed or
# read into memory. CSV is row-based and untyped-at-rest, so no such
# pushdown is possible: Spark must read and parse every row, then filter
# in memory afterwards.
df_parquet_read = spark.read.parquet(f"{OUT_DIR}/processed_parquet")

t0 = time.time()
high_value_parquet = df_parquet_read.filter(F.col("Sales") > 500).count()
parquet_filter_time = time.time() - t0

df_csv_read = (
    spark.read
    .option("header", "true")
    .schema(df_modified.schema)   # Order Date round-trips as yyyy-MM-dd, Spark's default CSV date format
    .csv(f"{OUT_DIR}/processed_csv")
)

t0 = time.time()
high_value_csv = df_csv_read.filter(F.col("Sales") > 500).count()
csv_filter_time = time.time() - t0

print(f"\nRows with Sales > 500 (Parquet source): {high_value_parquet}  |  filter time: {parquet_filter_time:.3f}s")
print(f"Rows with Sales > 500 (CSV source)    : {high_value_csv}      |  filter time: {csv_filter_time:.3f}s")

print("\n--- Physical plan for the Parquet filter (look for PushedFilters) ---")
df_parquet_read.filter(F.col("Sales") > 500).explain(mode="formatted")


# ---------------------------------------------------------------------------
# STEP 10 — File size comparison on disk
# ---------------------------------------------------------------------------
import subprocess
csv_size = subprocess.run(
    ["du", "-sh", f"{OUT_DIR}/processed_csv"], capture_output=True, text=True
).stdout.split()[0]
parquet_size = subprocess.run(
    ["du", "-sh", f"{OUT_DIR}/processed_parquet"], capture_output=True, text=True
).stdout.split()[0]
print(f"\nprocessed_csv size     : {csv_size}")
print(f"processed_parquet size : {parquet_size}  (columnar + compressed, partitioned by Region)")


# ---------------------------------------------------------------------------
# STEP 11 — Best practice reminder: show() over collect()
# ---------------------------------------------------------------------------
# NEVER call .collect() on a large DataFrame -- it pulls every row back to
# the single Driver's memory and will OOM-crash the Driver on real data
# volumes. .show(n) asks executors to compute and return only n rows.
print("\n--- Top 5 rows via .show() (safe) instead of .collect() (unsafe at scale) ---")
region_category_summary.show(5)

spark.stop()
print("\nSparkSession stopped. Pipeline complete.")
