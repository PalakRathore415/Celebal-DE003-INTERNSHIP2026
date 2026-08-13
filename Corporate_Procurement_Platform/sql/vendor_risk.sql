-- ============================================================
-- vendor_risk.sql
-- Corporate Procurement Platform
-- Vendor risk classification and expired contract queries.
-- ============================================================

-- 1. Full Vendor Risk Table --------------------------------------------------
SELECT
    vendor_id,
    vendor_name,
    category,
    region,
    late_payment_rate,
    avg_abs_variance_pct,
    contract_expired,
    risk_score,
    risk_category
FROM procurement_gold.gold_vendor_risk
ORDER BY risk_score DESC;


-- 2. High Risk Vendors Only ---------------------------------------------------
SELECT vendor_id, vendor_name, category, risk_score, risk_category
FROM procurement_gold.gold_vendor_risk
WHERE risk_category = 'High'
ORDER BY risk_score DESC;


-- 3. Expired Contracts (join back to the SCD2 table for full context) --------
WITH expired AS (
    SELECT vendor_id, unit_price, valid_from, valid_to
    FROM procurement_silver.silver_vendor_contracts_scd2
    WHERE is_current = true
      AND valid_to < CURRENT_DATE()
)
SELECT
    e.vendor_id,
    v.vendor_name,
    v.category,
    e.unit_price AS last_known_price,
    e.valid_from,
    e.valid_to,
    DATEDIFF(CURRENT_DATE(), e.valid_to) AS days_since_expiry
FROM expired e
JOIN procurement_silver.silver_vendors v
    ON e.vendor_id = v.vendor_id
ORDER BY days_since_expiry DESC;


-- 4. Risk Category Breakdown (count + total exposure) ------------------------
SELECT
    r.risk_category,
    COUNT(*) AS vendor_count,
    ROUND(SUM(s.total_po_amount), 2) AS total_spend_exposure
FROM procurement_gold.gold_vendor_risk r
JOIN procurement_gold.gold_vendor_spend s
    ON r.vendor_id = s.vendor_id
GROUP BY r.risk_category
ORDER BY
    CASE r.risk_category
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        ELSE 3
    END;


-- 5. Late Payment Leaderboard --------------------------------------------------
SELECT
    v.vendor_id,
    v.vendor_name,
    COUNT(i.invoice_id) AS total_invoices,
    SUM(CASE WHEN i.days_late > 0 THEN 1 ELSE 0 END) AS late_invoices,
    ROUND(SUM(CASE WHEN i.days_late > 0 THEN 1 ELSE 0 END) / COUNT(i.invoice_id) * 100, 1) AS late_pct
FROM procurement_silver.silver_invoices i
JOIN procurement_silver.silver_vendors v
    ON i.vendor_id = v.vendor_id
GROUP BY v.vendor_id, v.vendor_name
HAVING COUNT(i.invoice_id) >= 5
ORDER BY late_pct DESC;
