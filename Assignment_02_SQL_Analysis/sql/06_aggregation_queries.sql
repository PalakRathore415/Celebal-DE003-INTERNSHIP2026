USE celebal_week2;

-- Q13 Total number of orders
SELECT
COUNT(*) AS total_orders
FROM orders;


-- Q14 Revenue from Delivered Orders
SELECT
SUM(total_amount) AS delivered_revenue
FROM orders
WHERE status='Delivered';


-- Q15 Average price per category
SELECT
category,
ROUND(
AVG(unit_price),
2
) AS avg_price
FROM products
GROUP BY category;


-- Q16 Revenue and count by status
SELECT
status,
COUNT(*) AS total_orders,
SUM(total_amount) AS revenue
FROM orders
GROUP BY status
ORDER BY revenue DESC;


-- Q17 Maximum and Minimum product price
SELECT
category,
MAX(unit_price) AS highest_price,
MIN(unit_price) AS lowest_price
FROM products
GROUP BY category;


-- Q18 Categories with avg price > 2000
SELECT
category,
ROUND(
AVG(unit_price),
2
) AS avg_price
FROM products
GROUP BY category
HAVING AVG(unit_price)>2000;

-- Insight:
-- Delivered orders contribute highest revenue.

-- Insight:
-- Electronics category has higher average pricing.

-- Insight:
-- HAVING helps filter aggregated results.