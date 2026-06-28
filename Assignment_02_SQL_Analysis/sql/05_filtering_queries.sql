USE celebal_week2;

-- Q7: Delivered Orders
SELECT *
FROM orders
WHERE status='Delivered';


-- Q8: Electronics products above ₹2000
SELECT
product_name,
category,
unit_price
FROM products
WHERE category='Electronics'
AND unit_price>2000;


-- Q9: Maharashtra customers joined in 2024
SELECT
first_name,
last_name,
state,
join_date
FROM customers
WHERE state='Maharashtra'
AND join_date BETWEEN
'2024-01-01'
AND
'2024-12-31';


-- Q10: Orders between dates excluding cancelled
SELECT *
FROM orders
WHERE order_date
BETWEEN
'2024-08-10'
AND
'2024-08-25'
AND status!='Cancelled';