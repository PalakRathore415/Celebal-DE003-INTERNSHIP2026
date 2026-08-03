"""
Week 7 - Bonus: SCD Type 2 MERGE (history-preserving upsert)
===============================================================
The core assignment (delta_merge_pipeline.py) implements SCD Type 1:
an update simply overwrites the old value, no history kept. The
suggested screenshot folders (scd1/, scd2/) imply the instructor also
wants a Type 2 demonstration, so this script builds that as a bonus,
on a separate Delta table so it doesn't interfere with the Type 1
deliverable.

SCD Type 2 keeps every version of a row instead of overwriting it:
    - is_current   : True for the currently-active version of a customer
    - effective_date: when this version became active
    - end_date      : when this version was superseded (None if current)

Two-phase MERGE, the standard simplified pattern:
    Phase A (expire) : for customer_ids present in the incremental batch
                        AND currently active, MERGE sets is_current=False,
                        end_date=today on their *old* row.
    Phase B (insert)  : append a brand-new row for every incoming record
                        (both updates and new customers) with
                        is_current=True, effective_date=today, end_date=None.

Run:
    python delta_merge_scd2.py
"""

import shutil
import pandas as pd
from deltalake import DeltaTable, write_deltalake

DATA_DIR = "../data"
TABLE_PATH = "../delta_table/customers_scd2"
TODAY = pd.Timestamp.today().strftime("%Y-%m-%d")


def section(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


# ---------------------------------------------------------------------------
# Build the initial SCD2 table from the already-cleaned master data
# ---------------------------------------------------------------------------
section("Build initial SCD2 table from cleaned master data")

df_master = pd.read_csv(f"{DATA_DIR}/customer_master.csv").drop_duplicates(
    subset=["customer_id"], keep="first"
)
df_master["email"] = df_master["email"].fillna("unknown@example.com")
df_master["city"] = df_master["city"].fillna("Unknown")

df_master["effective_date"] = df_master["signup_date"]
df_master["end_date"] = pd.array([None] * len(df_master), dtype="string")
df_master["is_current"] = True

shutil.rmtree(TABLE_PATH, ignore_errors=True)
write_deltalake(TABLE_PATH, df_master, mode="overwrite")
dt = DeltaTable(TABLE_PATH)
print(f"Initial SCD2 table: {len(df_master)} rows, all is_current=True, version {dt.version()}")


# ---------------------------------------------------------------------------
# Phase A — expire the old version of every customer in the incremental batch
# ---------------------------------------------------------------------------
section("Phase A — expire old rows for customers being updated")

df_incremental = pd.read_csv(f"{DATA_DIR}/customer_incremental.csv")
expire_source = df_incremental[["customer_id"]].copy()
expire_source["end_date"] = TODAY

(
    dt.merge(
        source=expire_source,
        predicate="t.customer_id = s.customer_id AND t.is_current = true",
        source_alias="s",
        target_alias="t",
    )
    .when_matched_update(
        updates={"is_current": "false", "end_date": "s.end_date"}
    )
    .execute()
)
print(f"Expire commit done. Delta version: {dt.version()}")
expired_count = (dt.to_pandas()["is_current"] == False).sum()  # noqa: E712
print(f"Rows now marked is_current=False: {expired_count} "
      f"(expected: customers in the incremental batch that already existed)")


# ---------------------------------------------------------------------------
# Phase B — append a fresh current-version row for every incoming record
# ---------------------------------------------------------------------------
section("Phase B — insert new current-version rows")

new_versions = df_incremental.copy()
new_versions["effective_date"] = TODAY
new_versions["end_date"] = pd.array([None] * len(new_versions), dtype="string")
new_versions["is_current"] = True

write_deltalake(TABLE_PATH, new_versions, mode="append")
dt = DeltaTable(TABLE_PATH)
print(f"Appended {len(new_versions)} new current-version rows. Delta version: {dt.version()}")


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
section("Validate SCD2 table")

final = dt.to_pandas()
current_view = final[final["is_current"] == True]  # noqa: E712

print(f"Total historical rows (all versions): {len(final)}")
print(f"Current rows (is_current=True): {len(current_view)}")
print(f"Duplicate customer_id among CURRENT rows: "
      f"{current_view['customer_id'].duplicated().sum()}  -> should be 0")

# Spot check: a customer that was updated should now have 2 rows (1 expired, 1 current)
sample_id = df_incremental.iloc[0]["customer_id"]
versions = final[final["customer_id"] == sample_id].sort_values("effective_date")
print(f"\nVersion history for {sample_id} ({len(versions)} version(s)):")
print(versions[["customer_id", "city", "status", "effective_date", "end_date", "is_current"]].to_string(index=False))


section("SCD1 vs SCD2 — the difference this demonstrates")
print("""
SCD Type 1 (delta_merge_pipeline.py): the old row is overwritten in place.
    After the MERGE you can only ever see the customer's LATEST city/status —
    the fact that CUST0035 used to live in Mumbai is gone.

SCD Type 2 (this script): the old row is kept, just marked is_current=False
    with an end_date. A new row is added for the new values. The full
    history of every change a customer ever had is queryable at any time —
    at the cost of the table growing with every update instead of staying
    the same size.
""")
