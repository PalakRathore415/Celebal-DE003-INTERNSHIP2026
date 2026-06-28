USE celebal_week2;

-- Q19 Order details with customer names

SELECT
o.order_id,
o.order_date,
c.first_name,
c.last_name,
o.total_amount
FROM orders o
INNER JOIN customers c
ON o.customer_id=c.customer_id;



-- Q20 All customers and their orders

SELECT
c.customer_id,
c.first_name,
c.last_name,
o.order_id,
o.status
FROM customers c
LEFT JOIN orders o
ON c.customer_id=o.customer_id;



-- Q21 Orders + Products + Items

SELECT
o.order_id,
p.product_name,
oi.quantity,
oi.unit_price,
oi.discount_pct
FROM orders o
JOIN order_items oi
ON o.order_id=oi.order_id
JOIN products p
ON oi.product_id=p.product_id;



-- Business Query 1
-- Top customers by spending

SELECT
c.customer_id,
CONCAT(
c.first_name,
' ',
c.last_name
) AS customer_name,
SUM(o.total_amount) total_spending
FROM customers c
JOIN orders o
ON c.customer_id=o.customer_id
GROUP BY
c.customer_id,
customer_name
ORDER BY total_spending DESC
LIMIT 5;



-- Business Query 2
-- Monthly sales trend

SELECT
DATE_FORMAT(
order_date,
'%Y-%m'
) AS month,
SUM(total_amount) total_sales
FROM orders
GROUP BY month
ORDER BY month;



-- Business Query 3
-- Top selling products

SELECT
p.product_name,
SUM(oi.quantity) units_sold
FROM order_items oi
JOIN products p
ON oi.product_id=p.product_id
GROUP BY p.product_name
ORDER BY units_sold DESC
LIMIT 5;

-- Insight:
-- Repeat customers generate larger revenue.

-- Insight:
-- Joins connect business entities and create usable reports.

-- Insight:
-- Product demand can guide inventory planning.