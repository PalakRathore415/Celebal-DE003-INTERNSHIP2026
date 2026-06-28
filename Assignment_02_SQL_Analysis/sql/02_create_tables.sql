USE celebal_week2;

CREATE TABLE customers(
customer_id INT PRIMARY KEY,
first_name VARCHAR(50) NOT NULL,
last_name VARCHAR(50) NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL,
city VARCHAR(50) NOT NULL,
state VARCHAR(50) NOT NULL,
join_date DATE NOT NULL,
is_premium BOOLEAN DEFAULT FALSE
);

CREATE TABLE products(
product_id INT PRIMARY KEY,
product_name VARCHAR(100),
category VARCHAR(50),
brand VARCHAR(50),
unit_price DECIMAL(10,2),
stock_qty INT
);

CREATE TABLE orders(
order_id INT PRIMARY KEY,
customer_id INT,
order_date DATE,
status VARCHAR(20),
total_amount DECIMAL(12,2),

FOREIGN KEY(customer_id)
REFERENCES customers(customer_id)
);

CREATE TABLE order_items(
item_id INT PRIMARY KEY,
order_id INT,
product_id INT,
quantity INT,
unit_price DECIMAL(10,2),
discount_pct DECIMAL(5,2),

FOREIGN KEY(order_id)
REFERENCES orders(order_id),

FOREIGN KEY(product_id)
REFERENCES products(product_id)
);