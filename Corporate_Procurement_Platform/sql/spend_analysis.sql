-- ============================================================
-- spend_analysis.sql
-- Corporate Procurement Platform
-- Vendor spend, ranking, and average procurement cost queries.
-- Run against procurement_gold / procurement_silver (Spark SQL / Databricks SQL).
-- ============================================================

-- 1. Total Spend by Vendor -------------------------------------------------
SELECT
    vendor_id,
    vendor_name,
    category,
    region,
    total_po_amount,
    total_invoiced_amount,
    po_count
FROM procurement_gold.gold_vendor_spend
ORDER BY total_po_amount DESC;


-- 2. Top 10 Vendors by Spend ------------------------------------------------
SELECT
    vendor_id,
    vendor_name,
    category,
    total_po_amount
FROM procurement_gold.gold_vendor_spend
ORDER BY total_po_amount DESC
LIMIT 10;


-- 3. Vendor Ranking (with dense_rank, per category) -------------------------
-- Ranks vendors within their own category rather than globally, so a small
-- but dominant office-supplies vendor isn't invisible next to a huge
-- raw-materials vendor.
WITH ranked AS (
    SELECT
        vendor_id,
        vendor_name,
        category,
        total_po_amount,
        DENSE_RANK() OVER (PARTITION BY category ORDER BY total_po_amount DESC) AS rank_in_category
    FROM procurement_gold.gold_vendor_spend
)
SELECT *
FROM ranked
WHERE rank_in_category <= 3
ORDER BY category, rank_in_category;


-- 4. Average Procurement Cost (overall, and per category) -------------------
WITH overall AS (
    SELECT
        'ALL' AS category,
        ROUND(AVG(po_amount), 2) AS avg_po_amount,
        ROUND(AVG(unit_price), 2) AS avg_unit_price
    FROM procurement_silver.silver_purchase_orders
),
by_category AS (
    SELECT
        item_category AS category,
        ROUND(AVG(po_amount), 2) AS avg_po_amount,
        ROUND(AVG(unit_price), 2) AS avg_unit_price
    FROM procurement_silver.silver_purchase_orders
    GROUP BY item_category
)
SELECT * FROM overall
UNION ALL
SELECT * FROM by_category
ORDER BY category;


-- 5. Vendor Spend Tier Classification (CASE WHEN) ----------------------------
SELECT
    vendor_id,
    vendor_name,
    total_po_amount,
    CASE
        WHEN total_po_amount >= 100000 THEN 'Strategic'
        WHEN total_po_amount >= 40000  THEN 'Preferred'
        WHEN total_po_amount >= 10000  THEN 'Standard'
        ELSE 'Tail Spend'
    END AS spend_tier
FROM procurement_gold.gold_vendor_spend
ORDER BY total_po_amount DESC;
