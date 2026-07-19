WITH customer_sales AS (
    SELECT
        customer_id,
        SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_sales
ORDER BY total_sales DESC
LIMIT 5;

WITH customer_sales AS (
    SELECT
        customer_id,
        SUM(sales) AS total_sales
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_sales
ORDER BY total_sales ASC
LIMIT 5;

SELECT
    customer_id,
    COUNT(order_id) AS total_orders
FROM orders
GROUP BY customer_id
HAVING COUNT(order_id) = 1;

SELECT *
FROM orders
WHERE sales >
(
    SELECT AVG(sales)
    FROM orders
);

WITH max_sales AS (
    SELECT
        customer_id,
        MAX(sales) AS highest_sale
    FROM orders
    GROUP BY customer_id
)

SELECT
    o.customer_id,
    o.order_id,
    o.sales
FROM orders o
JOIN max_sales m
ON o.customer_id = m.customer_id
AND o.sales = m.highest_sale
ORDER BY o.customer_id;