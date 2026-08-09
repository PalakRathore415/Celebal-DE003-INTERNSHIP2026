"""
Generate realistic e-commerce data with intentional data-quality issues.

The generator keeps relationships valid for the normal dataset:
- every order_items.order_id belongs to orders.order_id
- every order_items.product_id belongs to products.product_id
- every non-null orders.customer_id belongs to customers.customer_id

Referential-integrity failures are tested separately in tests/test_edge_cases.py.
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


SEED = 2026
random.seed(SEED)

STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
REGIONS = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]
CATEGORIES = {
    "Electronics": ["Mobile", "Laptop", "Accessories"],
    "Clothing": ["Men", "Women", "Kids"],
    "Home": ["Furniture", "Kitchen", "Decor"],
    "Books": ["Fiction", "Non-Fiction", "Academic"],
}
CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]


def random_date(start: datetime, end: datetime) -> datetime:
    """Return a random timestamp between start and end."""
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, seconds))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    """Write a list of dictionaries to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_customers(count: int = 600) -> list[dict]:
    """Generate customers, including approximately 2% invalid email addresses."""
    first_names = ["Aarav", "Ishita", "Kabir", "Meera", "Riya", "Arjun",
                   "Ananya", "Vihaan", "Sara", "Aditya", "Nisha", "Rahul"]
    last_names = ["Sharma", "Singh", "Gupta", "Verma", "Mehta", "Kapoor",
                  "Rathore", "Joshi", "Malhotra", "Khan"]

    rows = []
    start = datetime(2023, 1, 1)
    end = datetime(2026, 7, 31)

    for number in range(1, count + 1):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = name.lower().replace(" ", ".") + f"{number}@example.com"

        # Intentional issue: approximately 2% invalid emails.
        if number % 50 == 0:
            email = email.replace("@example.com", "")
        elif number % 50 == 1:
            email = email.replace("@", "")

        rows.append({
            "customer_id": f"C{number:05d}",
            "customer_name": name,
            "email": email,
            "registration_date": random_date(start, end).strftime("%Y-%m-%d"),
            "customer_type": random.choice(CUSTOMER_TYPES),
        })

    return rows


def generate_products(count: int = 500) -> list[dict]:
    """Generate products with intentional whitespace/case inconsistencies."""
    adjectives = ["Premium", "Classic", "Smart", "Essential", "Advanced", "Modern"]
    nouns = ["Phone", "Chair", "Notebook", "Headphones", "Shirt", "Lamp",
             "Cookware", "Backpack", "Monitor", "Novel"]

    rows = []
    for number in range(1, count + 1):
        category = random.choice(list(CATEGORIES))
        subcategory = random.choice(CATEGORIES[category])
        name = f"{random.choice(adjectives)} {random.choice(nouns)} {number}"
        cost = round(random.uniform(10, 800), 2)

        # Intentional formatting issues.
        if number % 40 == 0:
            name = f"  {name.lower()}  "
        elif number % 40 == 1:
            name = name.upper()
        elif number % 40 == 2:
            name = f" {name} "

        rows.append({
            "product_id": f"P{number:05d}",
            "product_name": name,
            "category": category,
            "subcategory": subcategory,
            "cost_price": cost,
        })

    return rows


def generate_orders(customers: list[dict], count: int = 1000) -> list[dict]:
    """Generate orders with approximately 5% missing customer IDs."""
    rows = []
    start = datetime(2025, 1, 1)
    end = datetime(2026, 7, 31)

    for number in range(1, count + 1):
        customer_id = random.choice(customers)["customer_id"]

        # Intentional issue: approximately 5% NULL/empty customer IDs.
        if number % 20 == 0:
            customer_id = "" if number % 40 == 0 else "NULL"

        order_dt = random_date(start, end)

        # Intentional issue: some dates use DD-MM-YYYY.
        if number % 33 == 0:
            date_text = order_dt.strftime("%d-%m-%Y %H:%M:%S")
        else:
            date_text = order_dt.strftime("%Y-%m-%d %H:%M:%S")

        rows.append({
            "order_id": f"O{number:06d}",
            "customer_id": customer_id,
            "order_date": date_text,
            "status": random.choices(
                STATUSES,
                weights=[25, 15, 45, 8, 7],
                k=1
            )[0],
            "region_code": random.choice(REGIONS),
        })

    return rows


def generate_order_items(orders: list[dict], products: list[dict], count: int = 2500) -> list[dict]:
    """Generate order items. Approximately 3% have negative quantities (returns)."""
    rows = []

    for number in range(1, count + 1):
        order = random.choice(orders)
        product = random.choice(products)

        quantity = random.randint(1, 8)

        # Intentional issue/business event: negative quantity represents a return.
        if number % 33 == 0:
            quantity = -random.randint(1, 3)

        rows.append({
            "item_id": f"I{number:07d}",
            "order_id": order["order_id"],
            "product_id": product["product_id"],
            "quantity": quantity,
            "unit_price": round(random.uniform(20, 1200), 2),
            "discount_percent": round(random.uniform(0, 35), 2),
        })

    return rows


def generate_all(output_dir: str = "data/raw") -> None:
    """Generate all four source CSV files."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers)
    order_items = generate_order_items(orders, products)

    write_csv(directory / "customers.csv", customers,
              ["customer_id", "customer_name", "email", "registration_date", "customer_type"])
    write_csv(directory / "products.csv", products,
              ["product_id", "product_name", "category", "subcategory", "cost_price"])
    write_csv(directory / "orders.csv", orders,
              ["order_id", "customer_id", "order_date", "status", "region_code"])
    write_csv(directory / "order_items.csv", order_items,
              ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"])

    print(f"Generated {len(customers)} customers")
    print(f"Generated {len(products)} products")
    print(f"Generated {len(orders)} orders")
    print(f"Generated {len(order_items)} order items")


if __name__ == "__main__":
    generate_all()
