-- ============================================================
-- invoice_variance.sql
-- Corporate Procurement Platform
-- Invoice vs. contract price variance queries.
-- ============================================================

-- 1. Full Invoice Variance Detail -------------------------------------------
SELECT
    po_id,
    vendor_id,
    item_category,
    contract_unit_price,
    invoiced_unit_price,
    invoice_amount,
    variance_pct
FROM procurement_gold.gold_invoice_variance
WHERE variance_pct IS NOT NULL
ORDER BY ABS(variance_pct) DESC;


-- 2. Vendors Consistently Overbilling (avg variance > 10%) ------------------
-- Uses a CTE + HAVING to aggregate first, then filter on the aggregate.
WITH vendor_variance AS (
    SELECT
        v.vendor_id,
        v.vendor_name,
        ROUND(AVG(giv.variance_pct), 2) AS avg_variance_pct,
        COUNT(*) AS invoice_count
    FROM procurement_gold.gold_invoice_variance giv
    JOIN procurement_silver.silver_vendors v
        ON giv.vendor_id = v.vendor_id
    WHERE giv.variance_pct IS NOT NULL
    GROUP BY v.vendor_id, v.vendor_name
)
SELECT *,
    CASE
        WHEN avg_variance_pct > 0 THEN 'Overbilling'
        WHEN avg_variance_pct < 0 THEN 'Underbilling'
        ELSE 'On Contract'
    END AS variance_direction
FROM vendor_variance
WHERE ABS(avg_variance_pct) > 10
ORDER BY avg_variance_pct DESC;


-- 3. Invoice Variance Severity Buckets (CASE WHEN) ---------------------------
SELECT
    po_id,
    vendor_id,
    variance_pct,
    CASE
        WHEN variance_pct IS NULL THEN 'No Contract Match'
        WHEN ABS(variance_pct) <= 2  THEN 'Within Tolerance'
        WHEN ABS(variance_pct) <= 10 THEN 'Minor Variance'
        ELSE 'Major Variance'
    END AS variance_severity
FROM procurement_gold.gold_invoice_variance
ORDER BY ABS(COALESCE(variance_pct, 0)) DESC;


-- 4. Contract Price History for a Vendor (SCD2 in action) -------------------
-- Swap the vendor_id literal below to inspect any vendor's full price history.
SELECT
    vendor_id,
    unit_price,
    valid_from,
    valid_to,
    is_current
FROM procurement_silver.silver_vendor_contracts_scd2
WHERE vendor_id = 'V003'
ORDER BY valid_from;
