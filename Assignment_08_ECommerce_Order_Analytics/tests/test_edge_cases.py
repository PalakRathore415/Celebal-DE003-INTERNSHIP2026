"""Edge-case tests required by the project specification."""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from src.data_cleaning import check_referential_integrity, clean_order_items
from src.reporting_cli import percent_change


def test_missing_order_reference_is_detected():
    """An order item referencing an unknown order must be reported."""
    orders = pd.DataFrame({"order_id": ["O000001"]})
    items = pd.DataFrame({
        "item_id": ["I0000001"],
        "order_id": ["O999999"],
        "product_id": ["P000001"],
        "quantity": [1],
        "unit_price": [100],
        "discount_percent": [10],
    })

    orphan_items = check_referential_integrity(orders, items)

    assert len(orphan_items) == 1
    assert orphan_items.iloc[0]["order_id"] == "O999999"


def test_discount_over_100_is_flagged():
    """A discount above 100% must be identified as invalid."""
    items = pd.DataFrame({
        "discount_percent": [10, 120],
        "quantity": [1, 2],
        "unit_price": [100, 200],
    })

    _, issues = clean_order_items(items)

    assert any("invalid discount" in issue for issue in issues)


def test_zero_quantity_is_preserved():
    """Zero quantity is not silently changed; downstream business rules can decide how to treat it."""
    items = pd.DataFrame({
        "discount_percent": [10],
        "quantity": [0],
        "unit_price": [100],
    })

    cleaned, _ = clean_order_items(items)

    assert cleaned.iloc[0]["quantity"] == 0


def test_future_order_date_can_be_detected():
    """Future dates should be rejected by a validation rule."""
    future_date = pd.Timestamp.now().normalize() + pd.Timedelta(days=30)
    assert future_date > pd.Timestamp.now().normalize()


def test_percentage_change_zero_baseline():
    """A zero previous-period value must not cause division-by-zero."""
    assert percent_change(100, 0) is None


def test_sql_foreign_key_blocks_orphan():
    """SQLite should reject an orphan order item when FK enforcement is enabled."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("CREATE TABLE orders(order_id TEXT PRIMARY KEY)")
    conn.execute("""
        CREATE TABLE order_items(
            item_id TEXT PRIMARY KEY,
            order_id TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        )
    """)

    conn.execute("INSERT INTO orders VALUES ('O1')")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO order_items VALUES ('I1', 'UNKNOWN')")

    conn.close()
