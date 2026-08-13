"""
Synthetic data generator for the Corporate Procurement Platform project.
Original schema/design -- not copied from any reference repo.
Seeded for reproducibility.
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

REGIONS = ["North", "South", "East", "West"]
CATEGORIES = ["Raw Materials", "IT Equipment", "Office Supplies", "Logistics", "Packaging", "Consulting", "MRO Parts"]
DEPARTMENTS = ["Manufacturing", "IT", "Operations", "Finance", "HR", "Facilities", "R&D"]
VENDOR_NAME_PARTS = ["Sterling", "Vertex", "Orion", "Summit", "Crest", "Falcon", "Meridian", "Anchor",
                     "Nova", "Granite", "Horizon", "Pioneer", "Titan", "Everest", "Cascade", "Beacon",
                     "Zenith", "Pinnacle", "Atlas", "Vantage", "Quantum", "Redwood", "Sapphire", "Ironclad", "Northgate"]
VENDOR_SUFFIX = ["Industries", "Supplies Ltd", "Logistics", "Trading Co", "Materials", "Solutions", "Corp", "Enterprises"]

N_VENDORS = 25
today = date(2026, 8, 1)

def rand_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

# ---------- Vendors ----------
vendors = []
for i in range(1, N_VENDORS + 1):
    vid = f"V{i:03d}"
    name = f"{random.choice(VENDOR_NAME_PARTS)} {random.choice(VENDOR_SUFFIX)}"
    vendors.append({
        "vendor_id": vid,
        "vendor_name": name,
        "category": random.choice(CATEGORIES),
        "region": random.choice(REGIONS),
        "onboarded_date": rand_date(date(2019, 1, 1), date(2024, 1, 1)).isoformat(),
        "payment_terms_days": random.choice([15, 30, 45, 60]),
    })

with open("data/vendors.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=vendors[0].keys())
    w.writeheader()
    w.writerows(vendors)

# ---------- Vendor Contracts: 3 sequential batches (drives SCD2) ----------
# Each vendor has a base contract. ~40% renegotiate price at batch2, ~25% renegotiate again at batch3.
# A few vendors' contracts expire and are not renewed (tests "expired contract" gold logic).
base_contracts = {}
for v in vendors:
    base_contracts[v["vendor_id"]] = {
        "item_category": v["category"],
        "unit_price": round(random.uniform(50, 500), 2),
        "contract_start": date(2025, 1, 1).isoformat(),
        "contract_end": date(2026, 12, 31).isoformat(),
        "payment_terms": f"Net {v['payment_terms_days']}",
    }

batch_dates = [date(2025, 1, 1), date(2025, 7, 1), date(2026, 1, 1)]
renegotiate_at_2 = set(random.sample([v["vendor_id"] for v in vendors], k=10))
renegotiate_at_3 = set(random.sample(list(renegotiate_at_2), k=6))
expire_vendors = set(random.sample([v["vendor_id"] for v in vendors], k=3))

for batch_idx, batch_date in enumerate(batch_dates, start=1):
    rows = []
    cid_counter = 1
    for v in vendors:
        vid = v["vendor_id"]
        c = dict(base_contracts[vid])
        if batch_idx == 1:
            pass
        if batch_idx == 2 and vid in renegotiate_at_2:
            c["unit_price"] = round(c["unit_price"] * random.uniform(1.05, 1.25), 2)
            c["contract_start"] = date(2025, 7, 1).isoformat()
        if batch_idx == 3 and vid in renegotiate_at_3:
            c["unit_price"] = round(c["unit_price"] * random.uniform(0.95, 1.15), 2)
            c["contract_start"] = date(2026, 1, 1).isoformat()
        if batch_idx == 3 and vid in expire_vendors:
            c["contract_end"] = date(2026, 6, 30).isoformat()  # already expired vs "today"

        rows.append({
            "contract_id": f"C{cid_counter:03d}",
            "vendor_id": vid,
            "item_category": c["item_category"],
            "unit_price": c["unit_price"],
            "contract_start": c["contract_start"],
            "contract_end": c["contract_end"],
            "payment_terms": c["payment_terms"],
            "snapshot_date": batch_date.isoformat(),
        })
        cid_counter += 1
        if batch_idx == 2 and vid in renegotiate_at_2:
            base_contracts[vid]["unit_price"] = c["unit_price"]
        if batch_idx == 3 and vid in renegotiate_at_3:
            base_contracts[vid]["unit_price"] = c["unit_price"]

    with open(f"data/vendor_contracts_batch{batch_idx}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

# ---------- Purchase Orders ----------
pos = []
po_counter = 1
for _ in range(420):
    v = random.choice(vendors)
    order_date = rand_date(date(2025, 1, 1), date(2026, 7, 31))
    qty = random.randint(5, 500)
    unit_price = round(random.uniform(45, 520), 2)
    pos.append({
        "po_id": f"PO{po_counter:05d}",
        "vendor_id": v["vendor_id"],
        "order_date": order_date.isoformat(),
        "item_category": v["category"],
        "quantity": qty,
        "unit_price": unit_price,
        "po_amount": round(qty * unit_price, 2),
        "region": v["region"],
        "department": random.choice(DEPARTMENTS),
    })
    po_counter += 1

with open("data/purchase_orders.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=pos[0].keys())
    w.writeheader()
    w.writerows(pos)

# ---------- Invoices ----------
invoices = []
inv_counter = 1
for po in pos:
    if random.random() < 0.08:
        continue  # ~8% of POs have no invoice yet (in-flight orders)
    order_dt = date.fromisoformat(po["order_date"])
    invoice_date = order_dt + timedelta(days=random.randint(1, 20))
    if invoice_date > today:
        continue
    # invoice amount sometimes differs slightly from PO amount (variance)
    variance_factor = 1.0
    if random.random() < 0.25:
        variance_factor = random.uniform(0.9, 1.15)
    invoice_amount = round(po["po_amount"] * variance_factor, 2)

    vendor = next(v for v in vendors if v["vendor_id"] == po["vendor_id"])
    terms_days = vendor["payment_terms_days"]
    due_date = invoice_date + timedelta(days=terms_days)

    status_roll = random.random()
    if due_date > today:
        payment_status = "Pending"
        payment_date = ""
    elif status_roll < 0.75:
        payment_status = "Paid"
        payment_date = (due_date + timedelta(days=random.randint(-5, 3))).isoformat()
    elif status_roll < 0.92:
        payment_status = "Paid"
        payment_date = (due_date + timedelta(days=random.randint(4, 30))).isoformat()  # late payment
    else:
        payment_status = "Overdue"
        payment_date = ""

    invoices.append({
        "invoice_id": f"INV{inv_counter:05d}",
        "po_id": po["po_id"],
        "vendor_id": po["vendor_id"],
        "invoice_date": invoice_date.isoformat(),
        "invoice_amount": invoice_amount,
        "due_date": due_date.isoformat(),
        "payment_date": payment_date,
        "payment_status": payment_status,
    })
    inv_counter += 1

with open("data/invoices.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=invoices[0].keys())
    w.writeheader()
    w.writerows(invoices)

print(f"vendors: {len(vendors)}")
print(f"contract batches: 3 x {len(vendors)} rows")
print(f"purchase_orders: {len(pos)}")
print(f"invoices: {len(invoices)}")
