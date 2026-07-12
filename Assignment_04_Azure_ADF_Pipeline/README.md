# Assignment 04 – Azure Cloud Fundamentals and Data Pipeline Implementation using Azure Data Factory

## Overview

This project demonstrates the implementation of an end-to-end data pipeline using Microsoft Azure services. The pipeline uses Azure Blob Storage and Azure Data Factory (ADF) to ingest, validate, and copy the Superstore dataset from a source Blob container to a destination Blob container.

The assignment also covers Azure cloud fundamentals, resource management, Linked Services, Datasets, pipeline orchestration, metadata validation, monitoring, and role-based access control (IAM).

---

## Objectives

- Understand Azure cloud fundamentals.
- Create and manage Azure resources.
- Create an Azure Storage Account and Blob Container.
- Upload the Superstore dataset to Azure Blob Storage.
- Create Azure Data Factory.
- Configure Linked Services and Datasets.
- Retrieve file metadata using the Get Metadata activity.
- Build and execute a Copy Data pipeline.
- Monitor pipeline execution.
- Configure IAM roles for secure access.
- Implement a complete end-to-end Azure data pipeline.

---

## Azure Services Used

- Azure Resource Group
- Azure Storage Account
- Azure Blob Storage
- Azure Data Factory (ADF)
- Azure IAM (Role-Based Access Control)
- Azure Monitor

---

## Project Structure

```text
Assignment_04_Azure_ADF_Pipeline/
│
├── dataset/
│   └── Sample-Superstore.csv
│
├── pipeline/
│   ├── pipeline_steps.md
│   └── pipeline.json
│
├── results/
│   ├── 01_resource_group_created.png
│   ├── 02_storage_account_created.png
│   ├── 03_blob_container_created.png
│   ├── 04_csv_uploaded.png
│   ├── 05_adf_created.png
│   ├── 06_linked_service.png
│   ├── 07_datasets_created.png
│   ├── 08_get_metadata_activity.png
│   ├── 09_copy_data_pipeline.png
│   ├── 10_pipeline_debug_success.png
│   ├── 11_monitor_success.png
│   ├── 12_iam_roles.png
│   └── 13_end_to_end_pipeline.png
│
├── README.md
├── requirements.txt
└── Assignment_04_Report.docx
```

---

## Pipeline Architecture

```text
Sample-Superstore.csv
        │
        ▼
Azure Blob Storage
        │
        ▼
Azure Data Factory
   ├── Get Metadata
   └── Copy Data
        │
        ▼
Destination Blob Storage
```

---

## Pipeline Workflow

1. Upload the **Sample-Superstore.csv** dataset to Azure Blob Storage.
2. Create an Azure Data Factory instance.
3. Configure a Linked Service to connect ADF with Azure Blob Storage.
4. Create source and destination datasets.
5. Use the **Get Metadata** activity to validate the source file and retrieve metadata.
6. Configure the **Copy Data** activity to copy the dataset.
7. Execute the pipeline using **Debug** and **Trigger**.
8. Monitor the pipeline execution in the **Monitor** section.
9. Configure IAM roles to allow Azure Data Factory to access Azure Storage securely.
10. Validate successful data transfer to the destination container.

---

## Activities Performed

- Created an Azure Resource Group.
- Created an Azure Storage Account.
- Created a Blob Storage container.
- Uploaded the Superstore dataset.
- Created Azure Data Factory.
- Configured Linked Services.
- Created Source and Destination Datasets.
- Configured the Get Metadata activity.
- Built the Copy Data pipeline.
- Executed the pipeline using Debug and Trigger.
- Monitored successful pipeline execution.
- Assigned IAM roles.
- Validated the end-to-end data pipeline.

---

## Results

The Azure Data Factory pipeline executed successfully and copied the **Sample-Superstore.csv** file from the source Blob Storage container to the destination Blob Storage container.

The **Get Metadata** activity successfully validated the existence of the source file before initiating the copy operation. Pipeline monitoring confirmed successful execution, demonstrating an end-to-end Azure data integration workflow.

---

## Key Learnings

Through this assignment, I gained practical experience in:

- Azure cloud fundamentals
- Azure Resource Group management
- Azure Storage Account configuration
- Azure Blob Storage
- Azure Data Factory
- Linked Services
- Source and Destination Datasets
- Get Metadata activity
- Copy Data activity
- Pipeline monitoring and debugging
- Azure IAM and access management
- Building end-to-end cloud data pipelines

---

## Future Improvements

- Parameterize the pipeline to support multiple datasets.
- Integrate Data Flow for data transformation.
- Schedule pipelines using Triggers.
- Store pipeline logs in Azure Monitor or Log Analytics.
- Extend the solution using Azure Data Lake Storage Gen2.

---

## Author

**Palak Rathore**

B.Tech Computer Science Engineering

Dehradun Institute of Technology (DIT)

Celebal Technologies Internship Program 2026