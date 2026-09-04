# InvenSight — Stock Prediction 📈 & Retail Analytics

> End-to-End Data Engineering pipeline for retail inventory analytics & demand forecasting.
> **73,100 rows | 3 Store Categories | 20 Products | Jan 2022 - Jan 2023**

## 🎯 Problem Statement

Retail stores face two critical challenges:
1. **Inventory Mismanagement** - Not knowing how much stock to hold leads to over-stocking or under-stocking, causing revenue loss and waste.
2. **Demand Unpredictability** - Without data-driven forecasting, stores cannot anticipate seasonal/weather-driven demand spikes.

## Solution

InvenSight is a full-stack data engineering platform that:
- Ingests raw retail CSV data through a **PySpark ETL pipeline**
- Transforms it using **dbt SQL models** into analytics-ready tables in **DuckDB**
- Visualizes insights on an interactive **Streamlit dashboard** with login, stock alerts, and demand forecasting

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Data Warehouse | **DuckDB** | Fast local analytical database |
| Data Transformation | **dbt** | SQL-based data modeling |
| ETL Engine | **PySpark** | Distributed DataFrame ETL pipeline |
| Orchestration | **Python** | Pipeline runner |
| Dashboard | **Streamlit** | Interactive multi-page web app |

## Dashboard Pages

| Page | Description |
|---|---|
| Data Gateway | Upload CSV or select from 3 pre-built store datasets |
| Sales Overview | Revenue trends, category performance, fulfillment KPIs |
| Stock Alerts | UNDERSTOCK / OVERSTOCK / HEALTHY with urgency scoring |
| Demand Forecast | Actual vs forecasted units, seasonal & weather impact |
| Setup & Configure | Business profile & data source configuration |
| Admin Panel | User management, activity logs, analytics |

## How to Run

Install dependencies:
    pip install -r requirements.txt

Run ETL pipeline:
    python Scripts/run_pipeline.py --mode dbt

Launch dashboard:
    streamlit run Dashboard/app.py

## Resume Bullet Points

1. Built InvenSight, an end-to-end retail analytics platform processing 73K+ records using PySpark, DuckDB, dbt, and Streamlit
2. Engineered a modular PySpark ETL pipeline (Extract -> Transform -> Load) building 5 data models outputting to Parquet and DuckDB
3. Designed an automated stock alert system classifying products as UNDERSTOCK/OVERSTOCK/HEALTHY with urgency scoring
4. Built a multi-page Streamlit dashboard with authentication, real-time KPIs, demand forecast charts, and admin user management
