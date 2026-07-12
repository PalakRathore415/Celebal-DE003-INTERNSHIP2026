# Azure Data Factory Pipeline Steps

## Pipeline Name

PL_Copy_Superstore

## Objective

Build an end-to-end Azure Data Factory pipeline to copy the Superstore CSV dataset from a source Blob Storage container to a destination Blob Storage container while validating the source file using the Get Metadata activity.

---

## Pipeline Workflow

Source Blob Storage
        │
        ▼
Get Metadata Activity
        │
        ▼
Copy Data Activity
        │
        ▼
Destination Blob Storage

---

## Implementation Steps

### Step 1: Create Linked Service

A Linked Service was created to establish a connection between Azure Data Factory and Azure Blob Storage.

---

### Step 2: Create Source Dataset

A CSV dataset was created for the source file stored in the Blob Storage container.

---

### Step 3: Create Destination Dataset

A destination dataset was created to store the copied CSV file.

---

### Step 4: Configure Get Metadata Activity

The Get Metadata activity was configured to retrieve information about the source file before executing the copy operation.

Metadata retrieved:

- File Exists
- File Size
- Last Modified

---

### Step 5: Configure Copy Data Activity

The Copy Data activity was configured to copy the CSV file from the source container to the destination container.

---

### Step 6: Execute Pipeline

The pipeline was executed using the Debug option and later triggered manually.

---

### Step 7: Monitor Execution

The pipeline execution was monitored from the Monitor section of Azure Data Factory.

The pipeline completed successfully without errors.

---

## Outcome

The Superstore dataset was successfully copied from the source Blob Storage container to the destination container. Metadata validation confirmed the availability of the source file before the copy operation.