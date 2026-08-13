# Corporate Procurement Platform — Medallion Data Pipeline

An end-to-end Databricks pipeline that turns raw procurement CSVs (vendors,
purchase orders, invoices, and three vendor-contract snapshots) into
business-ready Gold tables — vendor spend, invoice-vs-contract variance,
vendor risk scoring, region-wise spend, and monthly trend — using a **Bronze →
Silver → Gold** medallion architecture, with **SCD Type 2** applied to vendor
contracts so price/term history is never lost.

```
Raw CSVs → Bronze (raw Delta) → Silver (cleaned + SCD2 history) → Gold (SQL analytics) → Power BI
```

See `docs/architecture_diagram.png` for the full picture.

## Project layout

```
notebooks/
  01_Bronze_Ingestion.py       Land raw CSVs as Delta tables (schema + ingestion metadata + row-count validation)
  02_Silver_Transformation.py  Clean, dedup, standardize; flag (not drop) data-quality issues
  03_SCD_Type2.py              Merge the 3 contract snapshots into a Type 2 history table
  04_Gold_Analytics.py         Build the 5 Gold tables consumed by SQL / Power BI

sql/
  spend_analysis.sql           Total vendor spend, top-10, per-category ranking, spend tiers
  invoice_variance.sql         Invoice vs. contract price variance, overbilling vendors, severity buckets
  vendor_risk.sql              Vendor risk table, high-risk list, expired contracts, late-payment leaderboard
  region_analysis.sql          Region-wise spend, region x category matrix, monthly trend

data/
  vendors.csv, purchase_orders.csv, invoices.csv,
  vendor_contracts_batch1/2/3.csv    Synthetic sample data (25 vendors) — 3 dated snapshots of the
                                      same contracts so the SCD2 notebook has real changes to merge

docs/
  architecture_diagram.png     Bronze → Silver → Gold → Consumption diagram
  generate_data.py             Script used to generate the sample data (seeded, reproducible)
```

## How the pipeline works

**01 — Bronze Ingestion**
Reads each raw CSV with schema inference, adds `_source_file` /
`_ingested_at` metadata columns, writes to Delta, and validates that the
row count written matches the row count read (fails loudly on mismatch
rather than silently under-loading). Driven by widgets
(`raw_base_path`, `bronze_db`) so it's rerunnable against any upload path.

**02 — Silver Transformation**
Cleans each Bronze table: trims/standardizes vendor names, casts types,
parses dates, dedups on natural keys keeping the latest `_ingested_at`
row. Purchase orders get a `_dq_amount_mismatch` flag (quantity × unit
price vs. stated `po_amount`) and invoices get a derived `days_late`
column — quality issues are flagged, not silently dropped. The three
contract snapshot batches are cleaned individually here; they are **not**
historized in this notebook (that's Silver's job — "clean and
trustworthy" — separate from history-building).

**03 — SCD Type 2 on Vendor Contracts**
The centerpiece. Seeds the SCD2 table from batch 1, then processes
batches 2 and 3 **in snapshot order**, one Delta `MERGE` per batch:
1. Close out current rows whose `unit_price`/`item_category` changed
   (`is_current = false`, `valid_to = <new snapshot_date>`)
2. Insert new current rows for changed vendors and brand-new vendors

This mirrors how a real pipeline would work — a new snapshot lands every
day/week and gets merged incrementally, rather than diffing the first and
last file. Ends with validation (exactly one current row per vendor, no
overlapping history) and a preview of a vendor with price history.

**04 — Gold Analytics**
Joins Silver + the current SCD2 contract rows into 5 Gold tables:
1. `gold_vendor_spend` — total PO value, invoiced value, PO count per vendor
2. `gold_invoice_variance` — invoiced unit price vs. current contract unit
   price, as `variance_pct`, per PO
3. `gold_vendor_risk` — a documented, weighted composite score (late
   payments 30 pts / invoice variance 25 pts / expired contract 25 pts /
   top-quartile spend 20 pts) bucketed into Low/Medium/High
4. `gold_region_spend` — spend, PO count, vendor count per region
5. `gold_monthly_trend` — PO spend and invoice count by month

## SQL layer

The `sql/` files are the Databricks SQL / Power BI-facing layer on top of
the Gold tables, using CTEs, `CASE WHEN`, window functions
(`DENSE_RANK`, `LAG`), and joins back to Silver/SCD2 where extra context
is needed (e.g. pulling full contract history for a flagged vendor, or
joining risk back to spend for exposure totals). These are the queries
you'd wire directly into Power BI as DirectQuery/dataset sources, or run
ad hoc in the Databricks SQL editor.

## Running it

1. Upload the `data/*.csv` files to a Databricks workspace path (default
   expected: `/FileStore/tables/procurement/` — override with the
   `raw_base_path` widget).
2. Run the notebooks in order: `01 → 02 → 03 → 04`. Each is parameterized
   via widgets (database names) so you can point them at different
   environments without editing code.
3. Run the `sql/*.sql` queries against the resulting `procurement_gold` /
   `procurement_silver` schemas, or connect Power BI to those tables.

`docs/generate_data.py` regenerates the sample CSVs if you want a larger
or reseeded dataset — it's a from-scratch synthetic generator (seeded with
`random.seed(42)` for reproducibility), not sourced from any external
dataset.

## Reference

Built with reference to the public example pipeline at
https://github.com/AnirudhSharma2/CEI26 for general medallion-architecture
structure; the notebooks, SCD2 merge logic, risk-scoring model, and SQL
above are original to this project.
