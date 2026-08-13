# Celebal Technologies Data Engineering Internship 2026 (DE003)

This repository contains all assignments and project work completed as part of the Celebal Technologies Data Engineering Internship program.

## Assignments

| # | Title | Link |
|---|-------|------|
| 01 | Basic Data Exploration and Cleaning using Pandas | [Assignment 01](./Assignment_01_Data_Cleaning/) |
| 02 | SQL Analysis and Querying | [Assignment 02](./Assignment_02_SQL_Analysis/) |
| 03 | SQL Analysis using Subqueries, CTEs, and Window Functions | [Assignment 03](./Assignment_03_SQL_Analysis/) |
| 04 | Azure Data Factory Pipeline Implementation | [Assignment 04](./Assignment_04_Azure_ADF_Pipeline/) |
| 05 | Spark Data Processing using PySpark | [Assignment 05](./Assignment_05_Spark_Data_Processing_using_PySpark/) |
| 06 | Spark Architecture Pipeline | [Assignment 06](./Assignment_06_Spark_Architecture/) |
| 07 | Delta Lake MERGE Implementation | [Assignment 07](./Assignment_07_Delta_Lake_MERGE/) |
| 08 | E-Commerce Order Analytics System | [Assignment 08](./Assignment_08_ECommerce_Order_Analytics/) |
| 09 | Corporate Procurement Platform | [Project](./Corporate_Procurement_Platform/) |

## Project 09 — Corporate Procurement Platform

An end-to-end data engineering pipeline built using **Databricks, PySpark, Delta Lake, and SQL** to process corporate procurement data including vendors, purchase orders, invoices, and vendor contracts.

### Architecture

The project follows the **Medallion Architecture**:

```text
Raw CSVs
    ↓
Bronze Layer
    ↓
Silver Layer
    ↓
SCD Type 2
    ↓
Gold Layer
    ↓
SQL Analytics / Power BI