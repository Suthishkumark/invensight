# InvenSight — Smart Stock Analytics & Demand Prediction

> End-to-End Data Engineering pipeline for retail inventory analytics.
> **73,100 rows | 5 stores | 20 products | Jan 2022 – Jan 2023**

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| Data Warehouse | **DuckDB** | Fast local analytical database |
| Data Transformation | **dbt** | SQL-based data modeling & testing |
| **ETL Engine** | **PySpark** | Distributed DataFrame ETL pipeline |
| Orchestration | **Python** | Pipeline runner (`run_pipeline.py`) |
| Dashboard | **Streamlit** | Interactive 3-page web app |

## Architecture

### PySpark ETL Pipeline (Primary)
```
retail_store.csv
      │
      ▼
[PySpark Extract]
      │  reads 73K rows with explicit schema
      ▼
[PySpark Transform]
  ├── stg_sales          (staging — clean columns, cast types, filter negatives)
  ├── dim_product        (dimension — product catalog)
  ├── fct_sales          (fact — revenue, fulfillment, stock gap)
  ├── mart_stock_alerts  (alert — UNDERSTOCK / OVERSTOCK / HEALTHY)
  └── mart_demand_forecast (forecast vs actual trend by season/weather)
      │
      ▼
[PySpark Load]
  ├── Parquet files → Output/parquet/
  └── DuckDB → analytics.* tables
      │
      ▼
[Streamlit Dashboard]
  ├── 📈 Sales Overview
  ├── 🚨 Stock Alerts
  └── 📊 Demand Forecast
```

### dbt Pipeline (Alternative)
```
retail_store.csv
      │
      ▼
[Python extract_load.py]
      │  loads 73K rows
      ▼
DuckDB → raw.sales
      │
      ▼
[dbt build]
  ├── stg_sales          (staging view — clean columns, cast types)
  ├── dim_product        (dimension table — product catalog)
  ├── fct_sales          (fact table — revenue, fulfillment, stock gap)
  ├── mart_stock_alerts  (alert table — UNDERSTOCK / OVERSTOCK / HEALTHY)
  └── mart_demand_forecast (forecast vs actual trend by season/weather)
      │
      ▼
[Streamlit Dashboard]
```

## Project Structure

```
InvenSight/
├── Data/
│   ├── retail_store.csv          # Raw source data (73K rows)
│   └── retail.duckdb             # DuckDB warehouse (generated)
├── etl/                          # PySpark ETL module
│   ├── __init__.py
│   ├── spark_session.py          # Spark session factory
│   ├── extract.py                # CSV → Spark DataFrame
│   ├── transform.py              # All 5 data models (stg → facts → marts)
│   ├── load.py                   # Write to Parquet + DuckDB
│   └── pipeline.py               # Main orchestrator
├── Scripts/
│   ├── extract_load.py           # Ingest CSV → DuckDB raw schema (dbt mode)
│   └── run_pipeline.py           # Unified runner (--mode pyspark|dbt)
├── dbt_retail/                   # dbt project (alternative pipeline)
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_sales.sql
│   │   └── marts/
│   │       ├── dim_product.sql
│   │       ├── fct_sales.sql
│   │       ├── mart_stock_alerts.sql
│   │       └── mart_demand_forecast.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── Dashboard/
│   └── app.py                    # Streamlit 3-page dashboard
├── Notebooks/
│   └── InvenSight_retail Store.py  # Original EDA + ML script
├── Output/                         # EDA charts + Parquet output
├── SQL/                            # Reference SQL queries
├── README.md
└── requirements.txt
```

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the PySpark ETL pipeline (recommended)
```bash
python -m etl.pipeline
```
Or via the unified runner:
```bash
python Scripts/run_pipeline.py --mode pyspark
```

### 3. Run with dbt (alternative)
```bash
python Scripts/run_pipeline.py --mode dbt
```

### 4. Launch the dashboard
```bash
streamlit run Dashboard/app.py
```

Open **http://localhost:8501** in your browser.

## PySpark ETL Details

The PySpark ETL pipeline replaces the dbt + DuckDB ingestion with a pure Python/Spark workflow:

| ETL Phase | Module | What it does |
|---|---|---|
| **Extract** | `etl/extract.py` | Reads `retail_store.csv` with explicit schema, parses date from `dd-MM-yyyy` |
| **Transform** | `etl/transform.py` | Builds all 5 models: `stg_sales` → `dim_product` → `fct_sales` → `mart_stock_alerts` + `mart_demand_forecast` |
| **Load** | `etl/load.py` | Writes each model to Parquet files + DuckDB `analytics.*` tables |

## Dashboard Pages

| Page | Description |
|---|---|
| 📈 **Sales Overview** | Revenue trends, category/store performance, fulfillment KPIs |
| 🚨 **Stock Alerts** | UNDERSTOCK / OVERSTOCK / HEALTHY status with filters + CSV export |
| 📊 **Demand Forecast** | Actual vs forecasted units, seasonality & weather impact, error trend |

## Resume Bullet Points

1. Built **InvenSight**, an end-to-end ETL pipeline processing 73K+ retail records using **PySpark**, **DuckDB**, **dbt**, and **Streamlit** with full pipeline automation
2. Engineered a modular **PySpark ETL** (Extract → Transform → Load) replicating 5 dbt data models with DataFrame operations, outputting to both Parquet and DuckDB
3. Designed an automated **stock alert system** flagging UNDERSTOCK (<30 days) and OVERSTOCK (>120 days) products across 5 stores and 20 products
4. Built a 3-page interactive **Streamlit dashboard** visualizing revenue trends, stock health distribution, and actual vs forecasted demand by season and weather conditions
