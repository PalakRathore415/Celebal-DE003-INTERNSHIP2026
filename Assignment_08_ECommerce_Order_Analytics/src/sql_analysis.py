"""Python wrapper around the SQL analytics queries."""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd


def run_query(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = (),
) -> pd.DataFrame:
    """Execute a SELECT query and return its result as a DataFrame."""
    return pd.read_sql_query(query, conn, params=params)


def run_all_analysis(db_path: str = "ecommerce.db") -> None:
    """Run a representative set of required advanced analyses."""
    conn = sqlite3.connect(db_path)

    queries = {
        "revenue_by_category": """
            SELECT p.category,
                   ROUND(SUM(oi.quantity * oi.unit_price *
                       (1 - oi.discount_percent / 100.0)), 2) AS revenue
            FROM order_items oi
            JOIN orders o ON o.order_id = oi.order_id
            JOIN products p ON p.product_id = oi.product_id
            WHERE o.status <> 'CANCELLED'
            GROUP BY p.category
            ORDER BY revenue DESC;
        """,
        "top_customers": """
            SELECT o.customer_id,
                   ROUND(SUM(oi.quantity * oi.unit_price *
                       (1 - oi.discount_percent / 100.0)), 2) AS revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.customer_id IS NOT NULL
              AND o.status <> 'CANCELLED'
            GROUP BY o.customer_id
            ORDER BY revenue DESC
            LIMIT 10;
        """,
        "at_risk_customers": """
            WITH gaps AS (
                SELECT customer_id,
                       julianday(date(order_date)) -
                       julianday(LAG(date(order_date)) OVER (
                           PARTITION BY customer_id ORDER BY date(order_date)
                       )) AS gap
                FROM orders
                WHERE customer_id IS NOT NULL
            )
            SELECT customer_id,
                   ROUND(AVG(gap), 2) AS average_gap_days
            FROM gaps
            WHERE gap IS NOT NULL
            GROUP BY customer_id
            HAVING AVG(gap) > 30
            ORDER BY average_gap_days DESC;
        """,
    }

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    with (output_dir / "analytics_results.txt").open("w", encoding="utf-8") as file:
        for name, query in queries.items():
            file.write(f"\n{name.upper()}\n{'-' * len(name)}\n")
            result = run_query(conn, query)
            file.write(result.to_string(index=False))
            file.write("\n")

    conn.close()
    print("Analytics results saved to reports/analytics_results.txt")
