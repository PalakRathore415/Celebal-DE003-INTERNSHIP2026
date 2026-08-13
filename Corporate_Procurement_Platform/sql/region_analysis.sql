-- ============================================================
-- region_analysis.sql
-- Corporate Procurement Platform
-- Region-wise spend and monthly procurement trend queries.
-- ============================================================

-- 1. Region-Wise Spend ---------------------------------------------------------
SELECT
    region,
    total_spend,
    po_count,
    vendor_count,
    ROUND(total_spend / po_count, 2) AS avg_po_value
FROM procurement_gold.gold_region_spend
ORDER BY total_spend DESC;


-- 2. Highest Spending Region (single-row answer) --------------------------------
SELECT region, total_spend
FROM procurement_gold.gold_region_spend
ORDER BY total_spend DESC
LIMIT 1;


-- 3. Region x Category Spend Matrix (JOIN + GROUP BY) ----------------------------
SELECT
    po.region,
    po.item_category,
    ROUND(SUM(po.po_amount), 2) AS total_spend,
    COUNT(po.po_id) AS po_count
FROM procurement_silver.silver_purchase_orders po
GROUP BY po.region, po.item_category
ORDER BY po.region, total_spend DESC;


-- 4. Monthly Procurement Trend ----------------------------------------------------
SELECT
    month,
    total_po_spend,
    po_count,
    invoice_count,
    ROUND(
        total_po_spend - LAG(total_po_spend) OVER (ORDER BY month), 2
    ) AS spend_change_vs_prior_month
FROM procurement_gold.gold_monthly_trend
ORDER BY month;


-- 5. Region Ranking by Spend per Vendor (efficiency view, CTE + CASE WHEN) --------
WITH region_stats AS (
    SELECT
        region,
        total_spend,
        vendor_count,
        ROUND(total_spend / vendor_count, 2) AS spend_per_vendor
    FROM procurement_gold.gold_region_spend
)
SELECT
    region,
    total_spend,
    vendor_count,
    spend_per_vendor,
    CASE
        WHEN spend_per_vendor >= 50000 THEN 'High Concentration'
        WHEN spend_per_vendor >= 20000 THEN 'Moderate Concentration'
        ELSE 'Diversified'
    END AS spend_concentration
FROM region_stats
ORDER BY spend_per_vendor DESC;
