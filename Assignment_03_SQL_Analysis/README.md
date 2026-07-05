# Assignment 03 – SQL Analysis using Subqueries, CTEs, and Window Functions

## Overview

This assignment focuses on analyzing the Superstore dataset using advanced SQL concepts. The objective was to perform data analysis by applying Subqueries, Common Table Expressions (CTEs), Window Functions, and Joins to answer real-world business questions. The project demonstrates how SQL can be used to transform raw sales data into meaningful business insights.

---

## Objectives

- Import the Superstore dataset into MySQL.
- Create normalized tables (`customers`, `orders`, and `products`) from the raw dataset.
- Populate the tables using `SELECT DISTINCT`.
- Perform data analysis using:
  - Subqueries
  - Common Table Expressions (CTEs)
  - Window Functions
  - JOIN operations
- Solve business-related analytical queries.
- Document the SQL scripts and query outputs.

---

## Tools & Technologies

- MySQL 8.0
- MySQL Workbench
- SQL
- Git & GitHub

---

## Project Structure

```
Assignment_03_SQL_Analysis/
│
├── dataset/
│   └── Sample-Superstore.csv
│
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_insert_data.sql
│   ├── 03_subqueries.sql
│   ├── 04_ctes.sql
│   ├── 05_window_functions.sql
│   ├── 06_final_query.sql
│   └── 07_business_queries.sql
│
├── results/
│   └── Query screenshots
│
├── README.md
├── requirements.txt
└── Assignment_03_Report.docx
```

---

## SQL Concepts Covered

- Data Import
- Table Creation
- Data Normalization
- INSERT INTO ... SELECT DISTINCT
- Subqueries
- Common Table Expressions (CTEs)
- Window Functions
  - ROW_NUMBER()
  - RANK()
- Aggregate Functions
- JOIN Operations
- Business Query Analysis

---

## Business Queries Solved

- Find orders with sales greater than the average sales.
- Find the highest-value order for each customer.
- Calculate total sales for every customer.
- Identify customers whose total sales are above average.
- Rank customers based on total sales.
- Assign row numbers to customer orders.
- Display the top 3 customers based on total sales.
- Identify the top 5 and bottom 5 customers.
- Find customers who placed only one order.
- Determine the highest order value for each customer.

---

## Results

The analysis successfully demonstrated the use of advanced SQL techniques to explore sales data and answer business-related questions. By combining Subqueries, CTEs, Window Functions, and JOIN operations, meaningful insights about customer performance and sales trends were obtained.

---

## Key Learnings

- Improved understanding of SQL query optimization and data analysis.
- Learned how CTEs simplify complex queries.
- Understood the practical use of Window Functions for ranking and partitioning data.
- Gained experience in normalizing raw datasets into multiple related tables.
- Enhanced GitHub project organization and documentation skills.

---

## Author

**Palak Rathore**

B.Tech CSE (Full Stack & DevOps)

Dehradun Institute of Technology

Celebal Technologies Internship Program 2026