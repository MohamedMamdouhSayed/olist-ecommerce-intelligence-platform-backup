# olist-ecommerce-intelligence-platform

Enterprise-grade End-to-End E-Commerce Intelligence Platform built on the Olist Brazilian E-Commerce Dataset. This repository is currently initialized for local development and team-ready project organization only; Kafka, Spark, dbt, machine learning, and cloud resources will be implemented in later phases.

## Project Overview

The platform will transform raw Olist CSV data into curated analytics and intelligence products through a modern data engineering stack. The long-term goal is to support batch and streaming ingestion, medallion data processing, governed warehouse models, business intelligence dashboards, APIs, and machine learning use cases.

## Architecture Overview

Planned data flow:

```text
CSV
  |
  v
Kafka
  |
  v
Bronze
  |
  v
Silver
  |
  v
dbt
  |
  v
Gold
  |
  v
Fabric Warehouse
  |
  v
Power BI
  |
  v
FastAPI
  |
  v
Machine Learning
```

The repository follows a medallion architecture:

- **Bronze:** Raw, immutable landing data.
- **Silver:** Cleaned, conformed, and quality-checked data.
- **Gold:** Business-ready aggregates and semantic outputs.

## Technology Stack

- Python
- Kafka
- PySpark
- Databricks
- Medallion Architecture
- dbt
- Microsoft Fabric Warehouse
- Power BI
- FastAPI
- Streamlit
- Machine Learning
- Docker
- Airflow

## Folder Structure

```text
olist-ecommerce-intelligence-platform/
├── airflow/
├── api/
├── configs/
├── dashboard/
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── dbt/
├── docker/
├── docs/
├── infrastructure/
├── ingestion/
├── ml/
├── notebooks/
├── processing/
├── requirements/
├── tests/
├── warehouse/
├── README.md
├── .gitignore
└── docker-compose.yml
```

## Setup Instructions

### 1. Create a Python Virtual Environment

From the project root:

```powershell
python -m venv .venv
```

### 2. Activate the Virtual Environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Upgrade Packaging Tools

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### 4. Install Dependencies

```powershell
pip install -r requirements/requirements-dev.txt
```

### 5. Configure Environment Variables

The starter local configuration lives in `configs/.env`.

Review and adjust these values for your local machine:

```text
PROJECT_NAME=olist-ecommerce-intelligence-platform
DATA_PATH=data/raw
BRONZE_PATH=data/bronze
SILVER_PATH=data/silver
GOLD_PATH=data/gold
KAFKA_BOOTSTRAP_SERVER=localhost:9092
KAFKA_TOPIC_ORDERS=orders
SPARK_APP_NAME=olist-data-platform
```

Application code should import centralized settings from `configs/settings.py` instead of reading environment variables directly.

## Local Development Instructions

Validate the configuration module:

```powershell
python -m configs.settings
```

Start local infrastructure placeholders when the services are fully configured in a future phase:

```powershell
docker compose up -d
```

Stop local services:

```powershell
docker compose down
```

## Next Development Phases

1. Infrastructure setup and developer tooling
2. Data understanding and profiling
3. Kafka ingestion design and implementation
4. Bronze layer landing strategy
5. Silver layer cleaning and validation
6. dbt model development
7. Gold layer data marts
8. Microsoft Fabric Warehouse integration
9. Machine learning experimentation and tracking
10. FastAPI service layer
11. Streamlit and Power BI dashboards
12. Deployment, monitoring, and operations
