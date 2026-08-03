"""
Week 7 - Steps 1-3 support: generate customer_master.csv (the existing
data, with intentional null/duplicate problems for the cleaning step)
and customer_incremental.csv (a mix of UPDATED existing customers and
brand-new customers, to drive the MERGE step).
"""

import random
import pandas as pd

random.seed(7)

CITIES = ["Delhi", "Mumbai", "Bengaluru", "Jaipur", "Hyderabad", "Pune", "Chennai", "Kolkata"]
STATUSES = ["Active", "Inactive", "Trial"]
FIRST_NAMES = ["Rahul", "Amit", "Priya", "Sneha", "Vikram", "Anjali", "Rohan", "Neha",
               "Karan", "Pooja", "Arjun", "Divya", "Manish", "Kavya", "Suresh", "Meera"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Iyer", "Nair", "Reddy", "Singh", "Kapoor"]

N_MASTER = 80

# ---------------------------------------------------------------------------
# customer_master.csv — the existing / current data
# ---------------------------------------------------------------------------
rows = []
for i in range(1, N_MASTER + 1):
    cid = f"CUST{i:04d}"
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    city = random.choice(CITIES)
    email = f"{name.lower().replace(' ', '.')}{i}@example.com"
    status = random.choice(STATUSES)
    signup_date = (pd.Timestamp("2023-01-01") + pd.Timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d")
    rows.append([cid, name, city, email, status, signup_date])

df_master = pd.DataFrame(rows, columns=["customer_id", "name", "city", "email", "status", "signup_date"])

# --- inject bad data for the cleaning step (Step 2) ---
missing_idx = df_master.sample(5, random_state=1).index
df_master.loc[missing_idx[:3], "email"] = None
df_master.loc[missing_idx[3:], "city"] = None

dupes = df_master.sample(4, random_state=2)
df_master = pd.concat([df_master, dupes], ignore_index=True)

df_master.to_csv("../data/customer_master.csv", index=False)

# ---------------------------------------------------------------------------
# customer_incremental.csv — new + updated records for the MERGE step
# ---------------------------------------------------------------------------
clean_master = df_master.drop_duplicates(subset=["customer_id"], keep="first")
existing_ids = clean_master["customer_id"].tolist()

# 12 existing customers get an UPDATE (status change and/or city change —
# simulates a customer moving city or upgrading from Trial to Active)
update_ids = random.sample(existing_ids, 12)
update_rows = []
for cid in update_ids:
    orig = clean_master[clean_master["customer_id"] == cid].iloc[0]
    new_city = random.choice([c for c in CITIES if c != orig["city"]])
    new_status = random.choice([s for s in STATUSES if s != orig["status"]])
    update_rows.append([
        cid, orig["name"], new_city, orig["email"], new_status,
        orig["signup_date"],
    ])

# 8 brand-new customers (INSERT)
new_rows = []
for j in range(1, 9):
    cid = f"CUST{N_MASTER + j:04d}"
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    city = random.choice(CITIES)
    email = f"{name.lower().replace(' ', '.')}{N_MASTER + j}@example.com"
    status = random.choice(STATUSES)
    signup_date = pd.Timestamp("2025").strftime("%Y-%m-%d")
    new_rows.append([cid, name, city, email, status, signup_date])

df_incremental = pd.DataFrame(
    update_rows + new_rows,
    columns=["customer_id", "name", "city", "email", "status", "signup_date"],
)
df_incremental.to_csv("../data/customer_incremental.csv", index=False)

print(f"customer_master.csv      : {len(df_master)} rows ({len(clean_master)} unique customer_id)")
print(f"customer_incremental.csv : {len(df_incremental)} rows "
      f"({len(update_ids)} updates to existing customers, {len(new_rows)} new customers)")
print(f"\nSample updates (customer_id, old -> new city/status):")
for cid in update_ids[:5]:
    orig = clean_master[clean_master["customer_id"] == cid].iloc[0]
    upd = df_incremental[df_incremental["customer_id"] == cid].iloc[0]
    print(f"  {cid}: {orig['city']}/{orig['status']}  ->  {upd['city']}/{upd['status']}")
