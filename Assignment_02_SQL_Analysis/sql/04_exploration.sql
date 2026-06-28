USE celebal_week2;

-- Preview data

SELECT *
FROM customers;

SELECT *
FROM products;

SELECT *
FROM orders;

SELECT *
FROM order_items;


-- Record counts

SELECT COUNT(*) AS total_customers
FROM customers;

SELECT COUNT(*) AS total_products
FROM products;

SELECT COUNT(*) AS total_orders
FROM orders;

SELECT COUNT(*) AS total_order_items
FROM order_items;