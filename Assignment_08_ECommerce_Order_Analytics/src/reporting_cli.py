"""
Command-line reporting tool.

Only Python's standard library + sqlite3 are used for the actual CLI database work,
as required by the assignment.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta


DB_PATH = "ecommerce.db"


def parse_date(value: str) -> datetime:
    """Validate a YYYY-MM-DD date supplied by the user."""
    return datetime.strptime(value, "%Y-%m-%d")


def period_bounds(report_type: str, start: datetime, end: datetime) -> tuple[datetime, datetime]:
    """Validate the requested reporting period."""
    report_type = report_type.lower()

    if report_type not in {"daily", "weekly", "monthly"}:
        raise ValueError("Report type must be daily, weekly, or monthly.")

    if start > end:
        raise ValueError("Start date cannot be after end date.")

    return start, end


def previous_period(start: datetime, end: datetime) -> tuple[datetime, datetime]:
    """Return an equal-length period immediately preceding the selected period."""
    duration = end - start
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - duration
    return previous_start, previous_end


def fetch_summary(conn: sqlite3.Connection, start: str, end: str) -> dict:
    """Return orders, revenue, unique customers and top three products."""
    summary_sql = """
        SELECT
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(
                oi.quantity * oi.unit_price *
                (1 - oi.discount_percent / 100.0)
            ), 0) AS revenue,
            COUNT(DISTINCT o.customer_id) AS unique_customers
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        WHERE date(o.order_date) BETWEEN date(?) AND date(?)
          AND o.status <> 'CANCELLED';
    """

    top_products_sql = """
        SELECT
            p.product_name,
            ROUND(SUM(
                oi.quantity * oi.unit_price *
                (1 - oi.discount_percent / 100.0)
            ), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE date(o.order_date) BETWEEN date(?) AND date(?)
          AND o.status <> 'CANCELLED'
        GROUP BY p.product_id, p.product_name
        ORDER BY revenue DESC
        LIMIT 3;
    """

    row = conn.execute(summary_sql, (start, end)).fetchone()
    top_products = conn.execute(top_products_sql, (start, end)).fetchall()

    return {
        "total_orders": row[0],
        "revenue": float(row[1] or 0),
        "unique_customers": row[2],
        "top_products": top_products,
    }


def percent_change(current: float, previous: float) -> float | None:
    """Calculate percentage change, safely handling a zero baseline."""
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def print_report(report_type: str, start: datetime, end: datetime) -> None:
    """Generate and print the requested summary report."""
    conn = sqlite3.connect(DB_PATH)

    current = fetch_summary(conn, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    prev_start, prev_end = previous_period(start, end)
    previous = fetch_summary(
        conn,
        prev_start.strftime("%Y-%m-%d"),
        prev_end.strftime("%Y-%m-%d"),
    )

    change = percent_change(current["revenue"], previous["revenue"])

    print("\n" + "=" * 62)
    print("E-COMMERCE ORDER ANALYTICS REPORT")
    print("=" * 62)
    print(f"Report type     : {report_type.title()}")
    print(f"Date range      : {start:%Y-%m-%d} to {end:%Y-%m-%d}")
    print(f"Total orders    : {current['total_orders']}")
    print(f"Revenue         : ${current['revenue']:,.2f}")
    print(f"Unique customers: {current['unique_customers']}")
    print(f"Previous period : {prev_start:%Y-%m-%d} to {prev_end:%Y-%m-%d}")

    if change is None:
        print("Revenue change  : N/A (previous period revenue is zero)")
    else:
        print(f"Revenue change  : {change:+.2f}%")

    print("\nTop 3 Products")
    print("-" * 62)
    for rank, (name, revenue) in enumerate(current["top_products"], 1):
        print(f"{rank}. {name:<40} ${revenue:,.2f}")

    print("=" * 62 + "\n")
    conn.close()


def main() -> None:
    """Interactive CLI entry point."""
    try:
        report_type = input("Report type (daily/weekly/monthly): ").strip().lower()
        start = parse_date(input("Start date (YYYY-MM-DD): ").strip())
        end = parse_date(input("End date (YYYY-MM-DD): ").strip())

        start, end = period_bounds(report_type, start, end)
        print_report(report_type, start, end)

    except ValueError as exc:
        print(f"Input error: {exc}")


if __name__ == "__main__":
    main()
