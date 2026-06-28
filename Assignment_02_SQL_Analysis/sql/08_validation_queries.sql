USE celebal_week2;

-- Validate customer count

SELECT
COUNT(*) AS customer_count
FROM customers;


-- Validate product count

SELECT
COUNT(*) AS product_count
FROM products;


-- Check duplicate emails

SELECT
email,
COUNT(*)
FROM customers
GROUP BY email
HAVING COUNT(*)>1;


-- Check invalid prices

SELECT *
FROM products
WHERE unit_price<=0;


-- Check missing customer references

SELECT
o.*
FROM orders o
LEFT JOIN customers c
ON o.customer_id=c.customer_id
WHERE c.customer_id IS NULL;


-- Validate delivered orders

SELECT
COUNT(*)
FROM orders
WHERE status='Delivered';

-- Insight:
-- No duplicate customers found.

-- Insight:
-- Data passed integrity checks.

-- Insight:
-- Referential constraints maintained.