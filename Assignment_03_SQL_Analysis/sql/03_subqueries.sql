USE celebal_assignment3;

SELECT *
FROM orders
WHERE sales > (
    SELECT AVG(sales)
    FROM orders
);

SELECT o.*
FROM orders o
WHERE sales = (
    SELECT MAX(sales)
    FROM orders
    WHERE customer_id = o.customer_id
);