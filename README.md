# Indian Crime Analytics Data Warehouse (ETL & Star Schema)

An end-to-end data engineering pipeline built using Python and pandas. This project ingests raw Indian crime data, city demographics, and prison statistics, transforms them into a normalized **Star Schema Data Warehouse**, and exports partitioned analytical datasets.

## Data Warehouse Architecture
The star schema decouples fact measurements from contextual dimensions to optimize query performance:
* **Fact Table:** `Fact_Crime_Incidents` (Partitioned by Year)
* **Dimension Tables:** `Dim_Time`, `Dim_Location`, `Dim_Victim`, `Dim_Offender`, `Dim_Crime_Profile`

## Tech Stack
* **Language:** Python 3
* **Data Processing:** pandas, numpy
* **Environment:** VS Code on Fedora Linux

## How to Run
1. Clone the repository:
   ```bash
   git clone https://github.com/ZiyadaliSayed/Crime_data_analytics.git
   cd Crime_data_analytics