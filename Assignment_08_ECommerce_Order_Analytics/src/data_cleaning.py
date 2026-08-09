"""
Data cleaning and validation layer.

Each cleaning function returns a cleaned DataFrame and a list of issues.
This makes the process auditable instead of silently modifying the data.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd


DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S")


def _parse_mixed_datetime(value) -> pd.Timestamp:
    """Parse the two date formats required by the assignment."""
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()

    for fmt in DATE_FORMATS:
        try:
            # Use Python's datetime parser for explicit formats.
            # pandas.Timestamp.strptime is not implemented in current pandas versions.
            from datetime import datetime
            return pd.Timestamp(datetime.strptime(text, fmt))
        except (ValueError, TypeError):
            continue

    return pd.NaT


def clean_orders(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Fix mixed date formats and standardize missing customer IDs."""
    cleaned = df.copy()
    issues: list[str] = []

    missing_before = cleaned["customer_id"].astype(str).str.strip().isin(["", "NULL", "nan"]).sum()
    if missing_before:
        issues.append(f"orders: {missing_before} missing customer_id values converted to NULL.")

    cleaned["customer_id"] = (
        cleaned["customer_id"]
        .astype("string")
        .str.strip()
        .replace({"": pd.NA, "NULL": pd.NA, "nan": pd.NA})
    )

    cleaned["order_date"] = cleaned["order_date"].apply(_parse_mixed_datetime)

    invalid_dates = cleaned["order_date"].isna().sum()
    if invalid_dates:
        issues.append(f"orders: {invalid_dates} invalid/unparseable order dates found.")

    cleaned["order_date"] = cleaned["order_date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return cleaned, issues


def clean_products(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Trim product names and normalize them to title case."""
    cleaned = df.copy()

    changed = (
        cleaned["product_name"].astype(str)
        != cleaned["product_name"].astype(str).str.strip().str.title()
    ).sum()

    cleaned["product_name"] = cleaned["product_name"].astype(str).str.strip().str.title()

    issues = [f"products: normalized {changed} product names."]
    return cleaned, issues


def validate_emails(df: pd.DataFrame) -> list[str]:
    """Return customer IDs whose emails do not match a basic email pattern."""
    pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    invalid_ids = []

    for _, row in df.iterrows():
        email = str(row["email"]).strip()
        if not pattern.match(email):
            invalid_ids.append(str(row["customer_id"]))

    return invalid_ids


def check_referential_integrity(
    orders: pd.DataFrame,
    order_items: pd.DataFrame
) -> pd.DataFrame:
    """Return order-item rows whose order_id does not exist in orders."""
    valid_order_ids = set(orders["order_id"].dropna().astype(str))
    mask = ~order_items["order_id"].astype(str).isin(valid_order_ids)
    return order_items.loc[mask].copy()


def clean_order_items(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Validate numeric fields and flag suspicious values."""
    cleaned = df.copy()
    issues: list[str] = []

    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="coerce")
    cleaned["unit_price"] = pd.to_numeric(cleaned["unit_price"], errors="coerce")
    cleaned["discount_percent"] = pd.to_numeric(cleaned["discount_percent"], errors="coerce")

    returns = (cleaned["quantity"] < 0).sum()
    if returns:
        issues.append(f"order_items: {returns} negative quantities retained as returns.")

    invalid_discount = (
        (cleaned["discount_percent"] < 0) |
        (cleaned["discount_percent"] > 100)
    ).sum()
    if invalid_discount:
        issues.append(f"order_items: {invalid_discount} invalid discount percentages found.")

    return cleaned, issues


def clean_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Standardize string columns and registration dates."""
    cleaned = df.copy()
    cleaned["customer_id"] = cleaned["customer_id"].astype(str).str.strip()
    cleaned["customer_name"] = cleaned["customer_name"].astype(str).str.strip()
    cleaned["email"] = cleaned["email"].astype(str).str.strip().str.lower()
    cleaned["registration_date"] = pd.to_datetime(
        cleaned["registration_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    return cleaned, []


def save_cleaned(
    raw_dir: str = "data/raw",
    cleaned_dir: str = "data/cleaned",
    report_path: str = "reports/data_quality_report.txt",
) -> None:
    """Clean all source files and save an auditable issue report."""
    raw = Path(raw_dir)
    cleaned_path = Path(cleaned_dir)
    cleaned_path.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(raw / "customers.csv")
    products = pd.read_csv(raw / "products.csv")
    orders = pd.read_csv(raw / "orders.csv", dtype={"customer_id": "string"})
    order_items = pd.read_csv(raw / "order_items.csv")

    customers, customer_issues = clean_customers(customers)
    products, product_issues = clean_products(products)
    orders, order_issues = clean_orders(orders)
    order_items, item_issues = clean_order_items(order_items)

    invalid_email_ids = validate_emails(customers)
    orphan_items = check_referential_integrity(orders, order_items)

    issues = customer_issues + product_issues + order_issues + item_issues
    issues.append(f"customers: {len(invalid_email_ids)} invalid emails found.")
    issues.append(f"order_items: {len(orphan_items)} orphan order references found.")

    # Missing customer IDs are allowed by the source specification, so they are
    # retained as NULL rather than inventing a customer identity.
    customers.to_csv(cleaned_path / "customers.csv", index=False)
    products.to_csv(cleaned_path / "products.csv", index=False)
    orders.to_csv(cleaned_path / "orders.csv", index=False)
    order_items.to_csv(cleaned_path / "order_items.csv", index=False)

    with Path(report_path).open("w", encoding="utf-8") as report:
        report.write("E-COMMERCE ORDER ANALYTICS - DATA QUALITY REPORT\n")
        report.write("=" * 58 + "\n\n")
        for issue in issues:
            report.write(f"- {issue}\n")

        report.write("\nInvalid customer IDs (emails):\n")
        for customer_id in invalid_email_ids:
            report.write(f"  - {customer_id}\n")

        report.write("\nOrphan order-item references:\n")
        if orphan_items.empty:
            report.write("  - None\n")
        else:
            for order_id in orphan_items["order_id"].astype(str).unique():
                report.write(f"  - {order_id}\n")

    print(f"Saved cleaned data to: {cleaned_path}")
    print(f"Saved quality report to: {report_path}")


if __name__ == "__main__":
    save_cleaned()
