# 📦 InvenSight — Comprehensive Project Explanation & Architecture Guide

---

## 📑 Table of Contents
1. [Executive Summary & Project Vision](#1-executive-summary--project-vision)
2. [The Core Business Problem Solved](#2-the-core-business-problem-solved)
3. [System Architecture & Modern Data Stack](#3-system-architecture--modern-data-stack)
4. [Data Modeling & Pipeline Design (Star Schema)](#4-data-modeling--pipeline-design-star-schema)
5. [Multi-Category Store Intelligence (Plug & Play)](#5-multi-category-store-intelligence-plug--play)
6. [Interactive Enterprise Features](#6-interactive-enterprise-features)
7. [Futuristic Scope & Business Value](#7-futuristic-scope--business-value)
8. [Interview, Viva & Resume Presentation Guide](#8-interview-viva--resume-presentation-guide)

---

## 1. Executive Summary & Project Vision

**InvenSight** is an end-to-end, AI-powered Retail Analytics & Inventory Optimization Platform designed to help modern retail businesses eliminate stockouts, prevent inventory overstocking, and forecast customer demand in real time.

Built on the **Modern Data Stack (MDS)**—leveraging **DuckDB**, **dbt**, **PySpark**, and **Streamlit**—InvenSight transforms raw transactional logs into actionable business telemetry, automated stock risk alerts, and dynamic demand forecasting across multiple store branches.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Raw Retail    │ ────▶ │ DuckDB / dbt /  │ ────▶ │  Interactive    │
│  Transactions   │       │   PySpark ETL   │       │    Dashboard    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

## 2. The Core Business Problem Solved

Every year, the global retail sector loses over **$1.1 Trillion** due to inventory distortion:

### 🔴 1. Stockout Disasters (Understocking)
* **The Problem**: When high-demand items run out of stock, customers walk out and buy from competitors. Retailers suffer immediate revenue loss, brand dilution, and customer churn.
* **InvenSight Solution**: An automated **Understock Risk Engine** flags items with `< 30 days` of stock based on daily burn rates and assigns an **Urgency Score** to trigger purchase orders before shelves empty.

### 🟡 2. Dead Working Capital & Spoilage (Overstocking)
* **The Problem**: Over-ordering ties up critical working capital, incurs warehouse storage expenses, and causes severe spoilage in perishable categories (groceries, dairy, bakery, pharmaceuticals).
* **InvenSight Solution**: An automated **Overstock Risk Engine** flags items with `> 120 days` of stock, enabling managers to run targeted markdown promotions or discount campaigns.

### 🎯 3. Guesswork & Inaccurate Replenishment
* **The Problem**: Store managers order inventory based on gut feeling instead of analyzing weather changes, seasonal patterns, and promotional spikes.
* **InvenSight Solution**: Machine-learning-aligned **Demand Forecast Marts** compare actual vs. predicted units sold across weather conditions, seasons, and promotional days.

### 💱 4. Multi-Branch & Multi-Currency Complexity
* **The Problem**: Retail chains operating across diverse regions struggle to consolidate performance across different currencies and store types.
* **InvenSight Solution**: Real-time multi-currency conversion (`USD $`, `INR ₹`, `EUR €`, `GBP £`) and granular store performance telemetry.

---

## 3. System Architecture & Modern Data Stack

InvenSight employs a dual-pipeline architecture designed for both high-speed local analytical execution and distributed big data processing:

```
                              ┌───────────────────────────────────┐
                              │     Raw Retail Transaction Data   │
                              │     (CSV / Ingestion Gateway)     │
                              └─────────────────┬─────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
    ┌──────────────────────────┐                                  ┌──────────────────────────┐
    │     PySpark Pipeline     │                                  │   dbt + DuckDB Pipeline  │
    │  (Large Scale Distr.)    │                                  │    (Fast Columnar SQL)   │
    └────────────┬─────────────┘                                  └────────────┬─────────────┘
                 │                                                             │
                 │   [Extract]  ─ Raw CSV to DataFrames                        │   [Extract]  ─ Raw CSV to DuckDB
                 │   [Transform]─ Staging ➔ Dimensions ➔ Facts ➔ Marts        │   [Transform]─ dbt build (Star Schema)
                 │   [Load]     ─ Parquet & DuckDB Analytics                   │   [Load]     ─ Materialized Tables
                 │                                                             │
                 └──────────────────────────────┬──────────────────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │       DuckDB Data Warehouse       │
                              │    (High-Speed Columnar Engine)   │
                              └─────────────────┬─────────────────┘
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │  InvenSight Streamlit Dashboard   │
                              │ 📈 Sales  • 🚨 Alerts • 📊 Demand │
                              │ 💱 Currency • 🛡️ Admin & Audit    │
                              └───────────────────────────────────┘
```

### Technology Highlights:
* **DuckDB**: Embedded, high-performance in-process columnar SQL database that queries millions of records in milliseconds without server overhead.
* **dbt (data build tool)**: Industry-standard SQL modeling framework enabling modular transformations, documentation, and schema testing.
* **PySpark**: Distributed data processing engine capable of scaling ETL to big-data volumes.
* **Streamlit**: Modern interactive web interface with custom CSS design tokens, glassmorphic cards, and 60 FPS HTML5 canvas animations.
* **SQLite Security Engine**: SHA-256 password hashing, session tokens, and automated user activity audit logs.

---

## 4. Data Modeling & Pipeline Design (Star Schema)

InvenSight transforms raw transactional data into a pristine **Star Schema** dimensional model:

```
                       ┌─────────────────────────┐
                       │   analytics.dim_product │
                       ├─────────────────────────┤
                       │  PK  product_id         │
                       │      category           │
                       │      base_price         │
                       └────────────┬────────────┘
                                    │ 1
                                    │
                                    │ N
                       ┌────────────┴────────────┐
                       │   analytics.fct_sales   │
                       ├─────────────────────────┤
                       │  PK  sale_id            │
                       │      sale_date          │
                       │  FK  store_id           │
                       │  FK  product_id         │
                       │      units_sold         │
                       │      revenue            │
                       │      stock_gap          │
                       │      fulfillment_rate   │
                       └────────────┬────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
┌───────────────────────────┐               ┌───────────────────────────┐
│ analytics.mart_stock_alerts│              │analytics.mart_demand_forecast│
├───────────────────────────┤               ├───────────────────────────┤
│ avg_inventory             │               │ actual_units              │
│ avg_units_sold            │               │ forecasted_units          │
│ days_of_stock             │               │ forecast_error            │
│ urgency_score             │               │ seasonality / weather     │
│ alert_status              │               │ holiday_promotion         │
└───────────────────────────┘               └───────────────────────────┘
```

### Key Mathematical Metrics:
1. **Revenue Calculation**:
   $$\text{Revenue} = \text{Units Sold} \times \text{Price} \times \left(1 - \frac{\text{Discount}}{100}\right)$$
2. **Stock Gap**:
   $$\text{Stock Gap} = \max(0, \text{Units Sold} - \text{Inventory Level})$$
3. **Fulfillment Rate**:
   $$\text{Fulfillment Rate} = \frac{\text{Units Sold}}{\text{Units Sold} + \text{Stock Gap}}$$
4. **Days of Stock**:
   $$\text{Days of Stock} = \frac{\text{Average Inventory}}{\text{Average Daily Units Sold}}$$
5. **Stock Alert Status**:
   $$\text{Status} = \begin{cases} \text{UNDERSTOCK} & \text{if Days of Stock} < 30 \\ \text{OVERSTOCK} & \text{if Days of Stock} > 120 \\ \text{HEALTHY} & \text{otherwise} \end{cases}$$

---

## 5. Multi-Category Store Intelligence (Plug & Play)

InvenSight is pre-configured with **7 authentic Kaggle-format retail datasets** stored in `Data/`:

| Store Category | Dataset File | Rows | Typical Categories | Best Used For |
| :--- | :--- | :---: | :--- | :--- |
| **🏪 General Retail** | `retail_store.csv` | 73,100 | Electronics, Clothing, Groceries, Toys, Furniture | Department stores & multi-line retail |
| **🛒 Supermarket & Grocery** | `supermarket_grocery_store.csv` | 15,000 | Fresh Produce, Dairy, Meat, Bakery, Beverages, Frozen | High-volume perishable FMCG analytics |
| **👗 Fashion & Apparel** | `fashion_apparel_store.csv` | 12,000 | Womenswear, Menswear, Footwear, Activewear, Accessories | Seasonal clothing & apparel retailers |
| **📱 Electronics & Gadgets** | `electronics_gadgets_store.csv` | 12,000 | Smartphones, Laptops, Audio, Gaming, Wearables | High-value, warranty-tracked tech retail |
| **💊 Pharmacy & Healthcare** | `pharmacy_healthcare_store.csv` | 12,000 | Prescription, OTC, Vitamins, Personal Care, Devices | Expiry-sensitive pharmaceutical stores |
| **🥐 Bakery & Cafe** | `bakery_cafe_store.csv` | 10,000 | Artisan Breads, Pastries, Cakes, Beverages, Savoury | Daily production & fresh food outlets |
| **🔧 Hardware & Home** | `hardware_home_store.csv` | 12,000 | Power Tools, Hand Tools, Plumbing, Electrical, Paints | Building supplies & home improvement |

---

## 6. Interactive Enterprise Features

1. **🚪 Data Ingestion Gateway**:
   * Users can upload any custom store CSV file or select any of the 7 pre-built store category datasets in 1 click.
2. **💱 Real-Time Currency Engine**:
   * Instant recalculation across `USD ($)`, `INR (₹)`, `EUR (€)`, and `GBP (£)` across all charts, KPIs, and reports.
3. **📊 Full-Fidelity Data Visualizations**:
   * Scaled units (Millions/Billions), unclipped axes, and clean tooltips.
4. **🛡️ Role-Based Access Control (RBAC)**:
   * Secure self-service registration and login.
   * Admin Panel with audit logs tracking every user's access timestamps, page views, and currency selections.
5. **💎 Deep Obsidian SaaS Theme**:
   * Premium glassmorphism aesthetics with 60 FPS HTML5 canvas neural particle constellation animations.

---

## 7. Futuristic Scope & Business Value

### Why InvenSight is Highly Futuristic:
* **Serverless Analytical Speed**: Using DuckDB in-process columnar execution avoids heavy cloud server costs while providing sub-second analytics on millions of rows.
* **Universal Domain Agnostic**: Works out-of-the-box for pharmacies, bakeries, supermarkets, and electronic shops without modifying core code.
* **Extensible to Real-Time IoT & ERP**: Architecture is ready to ingest live POS (Point of Sale) streams via Kafka/REST APIs.

### Future Roadmap Extensions:
1. **Automated Purchase Order (PO) Triggers**: Direct webhook integration with supplier ERPs (e.g. SAP, NetSuite) when an understock alert is raised.
2. **Reinforcement Learning Reorder Optimizer**: Dynamically adjusting reorder quantities based on lead times and shipping costs.
3. **Computer Vision Shelf Integration**: Connecting shelf camera feeds to compare physical on-shelf stock with system inventory records.

---

## 8. Interview, Viva & Resume Presentation Guide

### 🎙️ 60-Second Elevator Pitch:
> *"InvenSight is an end-to-end retail data intelligence platform built using DuckDB, dbt, and Streamlit. It solves the $1.1 Trillion problem of retail stockouts and inventory overstocking by automatically modeling 73K+ raw transaction records into a Star Schema warehouse, generating real-time inventory alerts, predicting seasonal demand trends, and delivering interactive multi-currency telemetry for store managers."*

### 💡 Common Interview Questions & Model Answers:

**Q1: Why did you choose DuckDB over traditional databases like MySQL or PostgreSQL?**
> *"Traditional relational databases (PostgreSQL/MySQL) are row-oriented (OLTP), designed for transactional processing. For analytical aggregations (SUM, AVG across millions of records), DuckDB's columnar vectorized engine executes queries 50x to 100x faster, in-process, without requiring a separate database server."*

**Q2: What is the purpose of dbt in this project?**
> *"dbt allows us to apply software engineering best practices to data modeling. It modularizes our SQL transformations into Staging, Dimension, Fact, and Mart layers, handles dependency graphs (DAGs), and ensures data quality through automated schema tests."*

**Q3: How does the Stock Alert model determine urgency?**
> *"The alert model computes 'Days of Stock' by dividing average inventory by average daily sales. If Days of Stock is under 30 days, it is classified as UNDERSTOCK. The Urgency Score is calculated using fulfillment deficit to prioritize which SKUs need immediate restocking."*

---

*InvenSight — Engineered for Intelligent Retail Operations.*
