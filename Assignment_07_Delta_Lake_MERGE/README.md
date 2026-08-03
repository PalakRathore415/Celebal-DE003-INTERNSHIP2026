# Assignment 07 — Delta Lake MERGE Implementation

**Celebal Technologies | Data Engineer Internship | Week 7**

## Objective

Perform incremental data processing using Delta Lake: load a customer
master table, clean it, merge in an incremental batch of new and
updated customers using the Delta Lake **MERGE** command, and validate
the result.

## How this was implemented

This project uses the official **`deltalake`** Python library
([delta-rs](https://github.com/delta-io/delta-rs), maintained by the
Delta Lake project under the Linux Foundation). It reads and writes
the real Delta Lake format — an actual `_delta_log/` transaction log,
Parquet data files, ACID commits, `MERGE`, and time travel — with
**no Spark cluster, no JVM, and no Databricks workspace required**.
Everything in this repo actually ran, end to end, and the numbers
below are the real output of that run.

A PySpark + `delta-spark` equivalent (the classic Databricks-style
API: `DeltaTable.forPath(spark, ...)`, `.whenMatchedUpdateAll()`) is
included as a reference appendix in the notebook — same MERGE logic,
same result, for whenever this needs to run on an actual Spark
cluster or in Databricks.

```bash
pip install deltalake pandas pyarrow
```

## Project Structure

```
Assignment_07_Delta_Lake_MERGE/
│
├── data/
│   ├── customer_master.csv        # existing data (84 rows, w/ nulls + duplicates on purpose)
│   └── customer_incremental.csv   # 12 updates + 8 new customers
│
├── notebooks/
│   ├── generate_data.py           # builds the two CSVs above
│   ├── delta_merge_pipeline.py    # Steps 1-6, SCD Type 1 (the core assignment)
│   ├── delta_merge_scd2.py        # bonus: SCD Type 2, history-preserving MERGE
│   └── delta_scd_assignment.ipynb # all of the above, combined and executed
│
├── delta_table/
│   ├── customers/                 # the real Delta table (SCD1) — _delta_log/ + parquet
│   └── customers_scd2/            # the real Delta table (SCD2 bonus)
│
├── screenshots/
│   ├── data_loading/ data_cleaning/ scd1/ scd2/ validation/ final_output/
│
├── report/
│   └── Week7_Report.docx
│
└── README.md
```

## How to run

```bash
cd notebooks
python generate_data.py           # writes data/customer_master.csv, customer_incremental.csv
python delta_merge_pipeline.py    # Steps 1-6: load -> clean -> merge -> validate -> display
python delta_merge_scd2.py        # bonus: SCD Type 2 version of the same merge
# or open delta_scd_assignment.ipynb in VS Code and Run All
```

## Results from the actual run

**Step 1-2 — Load + clean**
- `customer_master.csv`: 84 raw rows (80 unique `customer_id`, 4 exact duplicates, 2 missing `city`, 3 missing `email` — injected on purpose)
- After cleaning: 80 rows, 0 nulls, 0 duplicates. Delta version 0 → 1.

**Step 3-4 — Incremental + MERGE (SCD Type 1)**
- `customer_incremental.csv`: 20 rows — 12 match an existing `customer_id` (update), 8 are new (insert)
- MERGE result, straight from the real Delta transaction log (`dt.history()`):
  `num_target_rows_updated: 12, num_target_rows_inserted: 8, num_output_rows: 88`
- Delta version 1 → 2 (one atomic commit for the whole MERGE)

**Step 5 — Validation**
| Check | Result |
|---|---|
| Total row count = 80 existing + 8 new | 88 == 88 → **PASS** |
| Duplicate `customer_id` in final table | 0 → **PASS** |
| Spot-check an updated customer (CUST0035) reflects new city/status | Chennai/Trial → **PASS** |
| Spot-check a new customer (CUST0081) is present | present → **PASS** |

**Step 6 — Final table**: 88 rows, displayed and exported; full commit history visible via `dt.history()` (3 versions: initial load, cleaning, merge).

## Bonus — SCD Type 2

The suggested screenshot folders (`scd1/`, `scd2/`) implied a second,
history-preserving flavor of the merge was also wanted, so
`delta_merge_scd2.py` implements it on a separate Delta table
(`customers_scd2`) so it doesn't interfere with the core SCD1 deliverable:

- Phase A (expire): MERGE sets `is_current = False`, `end_date = today` on the *old* row of every customer being updated (12 rows).
- Phase B (insert): append a fresh row for every incoming record (update or new) with `is_current = True`.
- Result: 100 total historical rows, 88 currently active, 0 duplicates among current rows.
- Example — `CUST0035` now has 2 rows: Mumbai/Active (expired) and Chennai/Trial (current) — the SCD1 table only ever shows the current one.

## SCD1 vs SCD2 — why it matters

SCD Type 1 overwrites in place — simplest, smallest table, but history is gone the moment a MERGE runs. SCD Type 2 keeps every version with `effective_date`/`end_date`/`is_current` — the table grows with every change, but you can answer "what was this customer's city on any given date" at any point in the future. Both are legitimate MERGE patterns; which one to use is a business decision about whether historical state needs to be queryable.

## Why `deltalake` (delta-rs) instead of PySpark + delta-spark here

`configure_spark_with_delta_pip()` resolves the `delta-spark` jar from
Maven Central at Spark startup — this build environment's network is
restricted to package registries (PyPI, npm, GitHub) and doesn't
reach Maven Central, so that path isn't available here. Your own
machine has normal internet access, so the PySpark appendix in the
notebook will run there or in Databricks without any changes. The
`deltalake` library sidesteps this entirely since it's pure Python +
Rust, installed from PyPI, with no JVM dependency — which is also
just a genuinely simpler way to work with Delta Lake outside a Spark
cluster.
