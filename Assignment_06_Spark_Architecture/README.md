# Assignment 06 — Spark Architecture & Efficient Data Processing

**Celebal Technologies | Data Engineer Internship | Week 6**

## Objective

Understand Spark's architecture (Driver, Cluster Manager, Executors) and execution
modes, understand Lazy Evaluation and the DAG (lineage graph), and build an
efficient `read → transform → filter → write` pipeline over the Superstore
dataset — handling schema, nulls, and comparing CSV vs Parquet performance.

## Project Structure

```
Assignment_06_Spark_Architecture/
│
├── data/
│   ├── Sample - Superstore.csv      # source dataset (9,994 rows)
│   └── sample.parquet/              # same data, Parquet format (input demo)
│
├── notebooks/
│   ├── spark_architecture_pipeline.py     # pipeline as a runnable script
│   └── spark_architecture_pipeline.ipynb  # same pipeline, executed, with real outputs
│
├── outputs/
│   ├── processed_csv/               # pipeline output, single CSV file
│   ├── processed_parquet/           # pipeline output, partitioned by Region
│   └── screenshots/                 # console/UI screenshots for the report
│
├── report/
│   └── Week6_Report.docx            # conceptual Q&A answers (15 questions)
│
└── README.md
```

Run either file from inside `notebooks/` — both implement the identical pipeline:

```bash
cd notebooks
python spark_architecture_pipeline.py
# or open spark_architecture_pipeline.ipynb in VS Code (Jupyter extension) and Run All
```

## Spark Architecture — quick reference

| Component | Role |
|---|---|
| **Driver** | Runs `main()`, builds the DAG from your transformations, requests resources from the Cluster Manager, schedules tasks, collects results |
| **Cluster Manager** | Allocates resources across the cluster (Standalone, YARN, Kubernetes, Mesos). In this project, `master("local[*]")` makes the Driver act as its own single-node cluster manager |
| **Executors** | JVM processes on worker nodes that actually run tasks and hold cached data / shuffle files |
| **Client vs Cluster mode** | Client: Driver runs on the machine that submitted the job (outside the cluster) — good for interactive/notebook work. Cluster: Driver runs *inside* the cluster, managed alongside the Executors — better for unattended production jobs since it survives the submitting machine disconnecting |

## Pipeline sequence (what the code does, in order)

1. **SparkSession** created (`local[*]`) — this starts the Driver.
2. **Read** the CSV with an **explicit schema** (no `inferSchema`) and correct encoding; also read the pre-existing `sample.parquet` to show a schema-less Parquet read.
3. **Select** relevant columns and **filter** narrow predicates (`Sales > 0`, `Quantity > 0`).
4. **Null handling**: count nulls per column, then `dropna` on key columns.
5. **Modify**: rename `Sub-Category` → `SubCategory`, cast `Order Date` string → `date`, add derived columns `Profit Margin` and `Order Year`.
6. **Wide transformation**: `groupBy("Region", "Category")` + aggregations — this is the one step in the pipeline that triggers a **shuffle**.
7. **Inspect the DAG** with `.explain(mode="formatted")` without running anything new — proof that everything before this point was lazy.
8. **Write** results to Parquet (partitioned by `Region`) and to CSV.
9. **Read back** both formats and filter `Sales > 500` on each, comparing timing and inspecting `PushedFilters` in the physical plan.
10. **Compare file size** on disk (CSV vs Parquet).
11. Use `.show()` throughout instead of `.collect()`.

## Results from the actual run (this dataset, 9,994 source rows)

- After column selection + filtering (`Sales > 0`, `Quantity > 0`): **9,694 rows**; zero nulls found in the key columns on this dataset.
- Region × Category aggregation (top row): **East / Technology → $264,872.08 total sales, $47,439.56 total profit, 533 orders.**
- **File size**: `processed_csv` ≈ **1.4 MB** vs `processed_parquet` ≈ **328 KB** — roughly **4x smaller** with Parquet's columnar compression, even though Parquet also carries the `Region` partition folder overhead.
- **Filtered read** (`Sales > 500`) returned the same **1,151 rows** from both sources, but the Parquet physical plan shows `PushedFilters: [IsNotNull(Sales), GreaterThan(Sales,500.0)]` pushed into the `Scan parquet` node itself — the filter runs as part of the file scan. The CSV plan filters *after* a full row-by-row parse, since CSV has no per-block statistics to skip on.

## Performance concepts demonstrated

- **Lazy evaluation**: transformations (`select`, `filter`, `withColumn`, `groupBy`) only build the DAG; nothing executes until an action (`count()`, `show()`, `write`) is called. This lets Catalyst optimize the *whole* chain at once (predicate pushdown, column pruning, filter reordering) instead of running each line eagerly.
- **Shuffle**: `groupBy(...).agg(...)` is a wide transformation — matching keys can be on any partition, so Spark redistributes ("shuffles") data across partitions before aggregating. This is visible in the physical plan as `Exchange` nodes and is the most expensive operation in this pipeline.
- **Predicate pushdown**: Parquet's columnar, self-describing format lets Spark evaluate filters at the storage layer and skip whole row-groups that can't match, before any data reaches memory. CSV, being row-based and untyped-at-rest, can't support this — every row must be read and parsed first.

## Best practices followed

- Explicit schema on CSV read instead of `inferSchema` (single pass, correct types).
- `.show(n)` for inspection everywhere; `.collect()` is never called on the full dataset.
- `spark.sql.shuffle.partitions` tuned down from the default 200 to match this small dataset's size — 200 tiny shuffle partitions would add scheduling overhead with no benefit here.
- Output written to Parquet as the primary format (partitioned by `Region`), with CSV kept alongside only for human readability.
