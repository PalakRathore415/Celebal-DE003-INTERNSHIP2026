# Assignment 05 - Spark Data Processing using PySpark

## Objective

The objective of this assignment is to understand Apache Spark fundamentals and perform data cleaning, transformation, filtering, aggregation, and schema modification using PySpark DataFrames. The assignment demonstrates how Spark processes large datasets efficiently using in-memory computation.

---

## Technologies Used

- Python 3.13
- Apache Spark (PySpark)
- Jupyter Notebook
- VS Code

---

## Dataset

**Dataset:** Sample Superstore Dataset

The dataset contains retail sales information including:

- Orders
- Customers
- Products
- Categories
- Regions
- Sales
- Profit
- Quantity
- Discount

---

## Project Structure

```
Assignment_05_Spark_Data_Processing
│
├── data
│   └── Sample - Superstore.csv
│
├── notebooks
│   └── spark_data_processing.ipynb
│
├── outputs
│   ├── screenshots
│   └── processed_sales_summary.csv (optional)
│
├── report
│
└── README.md
```

---

## Tasks Performed

### 1. Spark Session Creation

- Created a local Spark session.
- Verified Spark installation and version.

### 2. Data Loading

- Loaded the Superstore dataset into a Spark DataFrame.
- Displayed sample records.
- Explored schema and column information.

### 3. Data Cleaning

- Removed duplicate records.
- Identified missing values.
- Replaced null values using `fillna()`.

### 4. Data Filtering

Applied multiple filtering conditions including:

- Sales greater than 500
- Furniture category
- West region
- Profit greater than 100
- Discount greater than 0.2
- Multiple filter conditions

### 5. Aggregation

Calculated:

- Total Records
- Total Sales
- Average Sales
- Minimum Sales
- Maximum Sales

### 6. GroupBy Operations

Performed category-wise and region-wise analysis using:

- Total Sales
- Average Profit
- Order Count

Applied filtering on aggregated results to identify high-performing regions.

### 7. Schema Modification

Performed:

- Column renaming
- Data type casting

### 8. Complete Data Processing Pipeline

Built an end-to-end Spark pipeline combining:

- Data cleaning
- Null handling
- Filtering
- Aggregation
- Sorting

---

## Key Spark Concepts Covered

- SparkSession
- DataFrames
- Immutability
- Filtering
- Aggregation
- GroupBy
- Wide Transformations
- Shuffle Operations
- Schema Modification
- Data Cleaning Pipeline

---

## Results

Successfully demonstrated:

- Data cleaning
- Business-based filtering
- Sales aggregation
- Category-wise analysis
- Region-wise analysis
- Schema transformation
- End-to-end Spark data processing workflow

---

## Insights

- Spark performs in-memory computation, making it significantly faster than traditional MapReduce for iterative workloads.
- Removing duplicate and null records improves data quality.
- Business filters help analyze specific product categories and regional performance.
- Aggregation functions provide meaningful sales insights.
- GroupBy operations summarize business performance effectively.
- Schema modifications ensure accurate data analysis.
- The complete pipeline demonstrates a real-world ETL workflow using Spark DataFrames.

---

## Note

The Spark data processing pipeline executed successfully and all transformations were validated using DataFrame outputs. Exporting the final results to CSV may require additional Hadoop configuration (`winutils.exe`) on Windows systems.

---

## Author

**Palak Rathore**

Celebal Technologies Internship 2026

Assignment 05 – Spark Data Processing using PySpark