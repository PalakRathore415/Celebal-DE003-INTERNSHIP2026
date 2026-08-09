-- E-COMMERCE ORDER ANALYTICS
-- Revenue = quantity * unit_price * (1 - discount_percent / 100)
-- Cancelled orders are excluded from revenue-oriented analysis.
-- Negative quantity is treated as a return and naturally reduces net revenue.

-- 1. Total revenue per category
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price *
        (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.status <> 'CANCELLED'
GROUP BY p.category
ORDER BY total_revenue DESC;


-- 2. Top 10 customers by total order value
SELECT
    o.customer_id,
    ROUND(SUM(oi.quantity * oi.unit_price *
        (1 - oi.discount_percent / 100.0)), 2) AS total_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.customer_id IS NOT NULL
  AND o.status <> 'CANCELLED'
GROUP BY o.customer_id
ORDER BY total_order_value DESC
LIMIT 10;


-- 3. Month-wise order count for the last 12 months
WITH max_date AS (
    SELECT date(MAX(order_date)) AS latest_date
    FROM orders
)
SELECT
    strftime('%Y-%m', o.order_date) AS order_month,
    COUNT(*) AS order_count
FROM orders o, max_date
WHERE date(o.order_date) >= date(max_date.latest_date, '-11 months')
GROUP BY order_month
ORDER BY order_month;


-- 4. Customers who placed orders but never had a delivered item
SELECT DISTINCT o.customer_id
FROM orders o
WHERE o.customer_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM orders delivered_order
      JOIN order_items oi ON oi.order_id = delivered_order.order_id
      WHERE delivered_order.customer_id = o.customer_id
        AND delivered_order.status = 'DELIVERED'
  );


-- 5. Products with more returns than purchases
WITH product_flow AS (
    SELECT
        oi.product_id,
        SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS purchases,
        SUM(CASE WHEN oi.quantity < 0 THEN ABS(oi.quantity) ELSE 0 END) AS returns
    FROM order_items oi
    GROUP BY oi.product_id
)
SELECT
    p.product_id,
    p.product_name,
    purchases,
    returns
FROM product_flow pf
JOIN products p ON p.product_id = pf.product_id
WHERE returns > purchases
ORDER BY returns DESC;


-- 6. Return rate per category
SELECT
    p.category,
    ROUND(
        100.0 * SUM(CASE WHEN oi.quantity < 0 THEN ABS(oi.quantity) ELSE 0 END)
        / NULLIF(SUM(ABS(oi.quantity)), 0),
        2
    ) AS return_rate_percent
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY return_rate_percent DESC;


-- 7. Running revenue by region and date
WITH daily AS (
    SELECT
        o.region_code,
        date(o.order_date) AS order_date,
        SUM(oi.quantity * oi.unit_price *
            (1 - oi.discount_percent / 100.0)) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status <> 'CANCELLED'
    GROUP BY o.region_code, date(o.order_date)
)
SELECT
    region_code,
    order_date,
    ROUND(daily_revenue, 2) AS daily_revenue,
    ROUND(
        SUM(daily_revenue) OVER (
            PARTITION BY region_code
            ORDER BY order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    ) AS running_total
FROM daily
ORDER BY region_code, order_date;


-- 8. Product ranking by category using DENSE_RANK
WITH revenue AS (
    SELECT
        p.category,
        p.product_name,
        SUM(oi.quantity * oi.unit_price *
            (1 - oi.discount_percent / 100.0)) AS total_revenue
    FROM products p
    JOIN order_items oi ON oi.product_id = p.product_id
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status <> 'CANCELLED'
    GROUP BY p.category, p.product_id, p.product_name
)
SELECT
    category,
    product_name,
    ROUND(total_revenue, 2) AS total_revenue,
    DENSE_RANK() OVER (
        PARTITION BY category ORDER BY total_revenue DESC
    ) AS rank_in_category
FROM revenue
ORDER BY category, rank_in_category;


-- 9. LAG: days between consecutive customer orders
WITH customer_orders AS (
    SELECT
        customer_id,
        date(order_date) AS order_date,
        LAG(date(order_date)) OVER (
            PARTITION BY customer_id ORDER BY order_date
        ) AS previous_order_date
    FROM orders
    WHERE customer_id IS NOT NULL
)
SELECT
    customer_id,
    order_date,
    previous_order_date,
    CAST(julianday(order_date) - julianday(previous_order_date) AS INTEGER) AS days_gap
FROM customer_orders
WHERE previous_order_date IS NOT NULL;


-- At-risk customers: average gap > 30 days
WITH gaps AS (
    SELECT
        customer_id,
        julianday(date(order_date)) -
        julianday(LAG(date(order_date)) OVER (
            PARTITION BY customer_id ORDER BY date(order_date)
        )) AS days_gap
    FROM orders
    WHERE customer_id IS NOT NULL
)
SELECT
    customer_id,
    ROUND(AVG(days_gap), 2) AS average_gap_days,
    'At Risk' AS risk_flag
FROM gaps
WHERE days_gap IS NOT NULL
GROUP BY customer_id
HAVING AVG(days_gap) > 30;


-- 10. Multi-level CTE: monthly customer revenue segmentation
WITH monthly_customer_revenue AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS month,
        SUM(oi.quantity * oi.unit_price *
            (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
      AND o.status <> 'CANCELLED'
    GROUP BY o.customer_id, month
),
segmented AS (
    SELECT
        customer_id,
        month,
        revenue,
        CASE
            WHEN revenue > 10000 THEN 'High'
            WHEN revenue >= 5000 THEN 'Medium'
            ELSE 'Low'
        END AS segment
    FROM monthly_customer_revenue
)
SELECT month, segment, COUNT(*) AS customer_count
FROM segmented
GROUP BY month, segment
ORDER BY month, segment;


-- 11. NTILE quartile segmentation by lifetime value
WITH lifetime AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price *
            (1 - oi.discount_percent / 100.0)) AS total_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
      AND o.status <> 'CANCELLED'
    GROUP BY o.customer_id
),
quartiles AS (
    SELECT
        customer_id,
        total_value,
        NTILE(4) OVER (ORDER BY total_value DESC) AS quartile
    FROM lifetime
)
SELECT
    customer_id,
    ROUND(total_value, 2) AS total_value,
    quartile,
    CASE quartile
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        ELSE 'Bronze'
    END AS quartile_label
FROM quartiles
ORDER BY quartile, total_value DESC;


-- 12. Year-over-year monthly revenue comparison
WITH monthly AS (
    SELECT
        strftime('%Y', o.order_date) AS year,
        strftime('%m', o.order_date) AS month,
        SUM(oi.quantity * oi.unit_price *
            (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status <> 'CANCELLED'
    GROUP BY year, month
),
with_previous AS (
    SELECT
        year,
        month,
        revenue,
        LAG(revenue, 12) OVER (ORDER BY year, month) AS prev_year_revenue
    FROM monthly
)
SELECT
    year,
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(prev_year_revenue, 2) AS prev_year_revenue,
    CASE
        WHEN prev_year_revenue IS NULL OR prev_year_revenue = 0 THEN NULL
        ELSE ROUND(100.0 * (revenue - prev_year_revenue) / prev_year_revenue, 2)
    END AS yoy_growth_percent
FROM with_previous
ORDER BY year, month;


-- 13. First and most recent purchased category
WITH purchases AS (
    SELECT
        o.customer_id,
        p.category,
        o.order_date,
        ROW_NUMBER() OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date
        ) AS first_rank,
        ROW_NUMBER() OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date DESC
        ) AS last_rank
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.customer_id IS NOT NULL
      AND o.status <> 'CANCELLED'
)
SELECT
    customer_id,
    MAX(CASE WHEN first_rank = 1 THEN category END) AS first_category,
    MAX(CASE WHEN last_rank = 1 THEN category END) AS latest_category,
    CASE
        WHEN MAX(CASE WHEN first_rank = 1 THEN category END)
          <> MAX(CASE WHEN last_rank = 1 THEN category END)
        THEN 'Yes'
        ELSE 'No'
    END AS category_shift
FROM purchases
GROUP BY customer_id;


-- 14. Cumulative distribution of customer revenue
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price *
            (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id IS NOT NULL
      AND o.status <> 'CANCELLED'
    GROUP BY o.customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        SUM(revenue) OVER (
            ORDER BY revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue,
        SUM(revenue) OVER () AS total_revenue
    FROM customer_revenue
)
SELECT
    customer_id,
    ROUND(revenue, 2) AS revenue,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(100.0 * cumulative_revenue / NULLIF(total_revenue, 0), 2) AS cumulative_percent
FROM ranked
ORDER BY revenue DESC;


-- 15. Cohort analysis and retention
WITH customer_orders AS (
    SELECT DISTINCT
        o.customer_id,
        date(o.order_date, 'start of month') AS order_month
    FROM orders o
    WHERE o.customer_id IS NOT NULL
      AND o.status <> 'CANCELLED'
),
cohorts AS (
    SELECT
        customer_id,
        MIN(order_month) OVER (PARTITION BY customer_id) AS cohort_month,
        order_month
    FROM customer_orders
),
activity AS (
    SELECT
        cohort_month,
        CAST(
            (strftime('%Y', order_month) - strftime('%Y', cohort_month)) * 12 +
            (strftime('%m', order_month) - strftime('%m', cohort_month))
            AS INTEGER
        ) AS month_number,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM cohorts
    GROUP BY cohort_month, month_number
),
cohort_size AS (
    SELECT
        cohort_month,
        active_customers AS month_0_customers
    FROM activity
    WHERE month_number = 0
)
SELECT
    a.cohort_month,
    a.month_number,
    a.active_customers,
    ROUND(100.0 * a.active_customers / NULLIF(c.month_0_customers, 0), 2) AS retention_rate
FROM activity a
JOIN cohort_size c ON c.cohort_month = a.cohort_month
WHERE a.month_number BETWEEN 0 AND 3
ORDER BY a.cohort_month, a.month_number;


-- 16. Frequently bought together
SELECT
    CASE WHEN oi1.product_id < oi2.product_id
         THEN oi1.product_id ELSE oi2.product_id END AS product_a,
    CASE WHEN oi1.product_id < oi2.product_id
         THEN oi2.product_id ELSE oi1.product_id END AS product_b,
    COUNT(DISTINCT oi1.order_id) AS times_bought_together
FROM order_items oi1
JOIN order_items oi2
  ON oi1.order_id = oi2.order_id
 AND oi1.product_id < oi2.product_id
GROUP BY
    CASE WHEN oi1.product_id < oi2.product_id
         THEN oi1.product_id ELSE oi2.product_id END,
    CASE WHEN oi1.product_id < oi2.product_id
         THEN oi2.product_id ELSE oi1.product_id END
ORDER BY times_bought_together DESC
LIMIT 20;
