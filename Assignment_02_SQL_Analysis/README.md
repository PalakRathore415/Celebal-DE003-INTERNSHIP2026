# SQL-Based Data Analysis using Filtering, Aggregation & Business Queries

**Celebal Summer Internship 2026 – Week 2 Assignment**

## Author
**Palak Rathore**
B.Tech CSE (Full Stack & DevOps)
Dehradun Institute of Technology

## Project Objective
The objective of this project is to analyze e-commerce sales data using SQL and extract meaningful business insights through filtering, aggregation, joins, and validation techniques.

This project simulates real-world business reporting where SQL is used to understand customer behavior, product performance, revenue trends, and data quality.

## Dataset

| Item | Details |
|------|---------|
| Dataset | Sample Superstore Dataset |
| Schema | E-Commerce relational schema (provided in internship task) |
| Tables | Customers, Products, Orders, Order Items |

## Tools & Technologies

| Tool | Purpose |
|------|---------|
| MySQL Workbench | Database design & querying |
| SQL | Data analysis |
| Git & GitHub | Version control |
| VS Code | Development environment |

## Database Schema

```
customers → orders → order_items ← products
```

**Tables:**
1. `customers`
2. `products`
3. `orders`
4. `order_items`

## Project Structure

```
Assignment_02_SQL_Analysis
│
├── data
│   └── Sample - Superstore.csv
│
├── sql
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_insert_data.sql
│   ├── 04_exploration.sql
│   ├── 05_filtering_queries.sql
│   ├── 06_aggregation_queries.sql
│   ├── 07_business_queries.sql
│   └── 08_validation_queries.sql
│
├── outputs
│   └── screenshots
│
├── report
│
└── README.md
```

## Tasks Performed

| # | Task | Details |
|---|------|---------|
| 1 | **Database Setup** | Created SQL database, designed relational schema, applied primary & foreign keys |
| 2 | **Data Loading** | Inserted customers, products, orders, and order items |
| 3 | **Data Exploration** | Previewed records, validated row counts, verified table relationships |
| 4 | **Filtering Analysis** | Status filtering, category filtering, date filtering, state-based filtering |
| 5 | **Aggregation Analysis** | `SUM()`, `COUNT()`, `AVG()`, `MAX()`, `MIN()`, `GROUP BY`, `HAVING` |
| 6 | **Business Analysis** | Revenue analysis, customer spending, monthly sales trends, product performance |
| 7 | **Data Validation** | Duplicate checks, null validation, referential integrity checks |

## Key Business Insights

- Delivered orders generated the highest revenue contribution.
- Electronics products showed higher average pricing.
- Customer order history helped identify top spending customers.
- Product sales trends indicated inventory planning opportunities.
- Database constraints ensured data consistency and integrity.

## Learning Outcomes

Through this project, I learned:
- SQL query writing and optimization
- Relational database design
- Aggregation and analytical queries
- Business-oriented data interpretation
- Data validation and quality checks
- Structuring SQL projects for production-style workflows

## Conclusion

This project demonstrates practical SQL skills used in data analysis workflows including database creation, querying, aggregation, validation, and business reporting. The analysis converts raw transactional data into actionable insights.

---
*Submitted as part of Celebal Summer Internship 2026*