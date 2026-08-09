"""SQLite database creation and CSV loading utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


DB_PATH = "ecommerce.db"


def create_database(
    cleaned_dir: str = "data/cleaned",
    db_path: str = DB_PATH,
) -> None:
    """Create a normalized SQLite schema and load cleaned CSV data."""
    cleaned = Path(cleaned_dir)

    customers = pd.read_csv(cleaned / "customers.csv")
    products = pd.read_csv(cleaned / "products.csv")
    orders = pd.read_csv(cleaned / "orders.csv")
    items = pd.read_csv(cleaned / "order_items.csv")

    # SQLite's foreign-key checks are disabled by default, so explicitly enable them.
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        conn.executescript("""
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT,
            registration_date DATE,
            customer_type TEXT CHECK(customer_type IN ('REGULAR','PREMIUM','VIP'))
        );

        CREATE TABLE products (
            product_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            cost_price REAL CHECK(cost_price >= 0)
        );

        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            region_code TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        );

        CREATE TABLE order_items (
            item_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL CHECK(unit_price >= 0),
            discount_percent REAL CHECK(discount_percent BETWEEN 0 AND 100),
            FOREIGN KEY(order_id) REFERENCES orders(order_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        );
        """)

        customers.to_sql("customers", conn, if_exists="append", index=False)
        products.to_sql("products", conn, if_exists="append", index=False)

        # Missing customer IDs are intentionally retained as NULL.
        orders.to_sql("orders", conn, if_exists="append", index=False)
        items.to_sql("order_items", conn, if_exists="append", index=False)

        conn.commit()

    print(f"SQLite database created: {db_path}")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
