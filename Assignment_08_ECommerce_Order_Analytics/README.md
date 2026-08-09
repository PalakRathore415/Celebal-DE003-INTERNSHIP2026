# E-Commerce Order Analytics System

A complete local data-engineering mini project for the Celebal Technologies Data Engineering Internship 2026.

## Project Objective

Build an end-to-end analytics workflow using Python and SQLite:

1. Generate realistic e-commerce CSV data with intentional data-quality issues.
2. Clean and validate the raw data with Pandas.
3. Load cleaned data into SQLite with primary/foreign-key constraints.
4. Execute basic, intermediate and advanced SQL analytics.
5. Provide a command-line reporting tool for daily/weekly/monthly summaries.
6. Test critical edge cases and referential integrity.
7. Produce a data-quality report documenting every issue detected.

## Source Requirements Covered

- `orders.csv`
- `order_items.csv`
- `products.csv`
- `customers.csv`
- Missing customer IDs
- Incorrect date formats
- Negative quantities representing returns
- Product-name formatting inconsistencies
- Invalid emails
- Referential-integrity validation
- Aggregations, joins, CTEs and window functions
- `DENSE_RANK`, `LAG`, `NTILE`, cumulative distribution
- Cohort analysis and retention
- Customer category segmentation
- Year-over-year comparison
- First/last category analysis
- Frequently bought-together analysis
- CLI reporting and previous-period comparison
- Edge-case tests

## Project Structure

```text
ecommerce_order_analytics/
├── data/
│   ├── raw/
│   └── cleaned/
├── reports/
│   └── data_quality_report.txt
├── sql/
│   └── analytics.sql
├── src/
│   ├── __init__.py
│   ├── data_generator.py
│   ├── data_cleaning.py
│   ├── database.py
│   ├── sql_analysis.py
│   └── reporting_cli.py
├── tests/
│   └── test_edge_cases.py
├── main.py
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the complete pipeline

```bash
python main.py
```

This will:

- generate raw CSV files,
- clean and validate them,
- create `ecommerce.db`,
- run the analytics queries,
- write a data-quality report.

## Run the CLI report separately

```bash
python -m src.reporting_cli
```

Example:

```text
Report type (daily/weekly/monthly): monthly
Start date (YYYY-MM-DD): 2026-01-01
End date (YYYY-MM-DD): 2026-01-31
```

## Design Decisions

### Revenue
Net revenue is calculated as:

`quantity × unit_price × (1 - discount_percent / 100)`

Cancelled orders are excluded from sales reporting. Negative quantities are retained because they represent returns and therefore reduce net revenue.

### Data quality
Cleaning is deliberately separated from generation. The generator creates realistic problems; the cleaning layer fixes or flags them; the database layer enforces structural integrity.

### Reproducibility
A fixed random seed is used so the generated dataset can be recreated consistently.

## Expected Deliverables

- Raw CSV files
- Cleaned CSV files
- SQLite database
- Data-quality report
- SQL analytics script
- CLI reporting tool
- Automated edge-case tests
