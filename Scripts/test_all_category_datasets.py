"""
Comprehensive Test Script: Validates all store category datasets through
ETL schema checks and analytics aggregations in DuckDB.
"""

import os
import sys
import duckdb
import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")

datasets = [
    ("General Retail", "retail_store.csv"),
    ("Supermarket & Grocery", "supermarket_grocery_store.csv"),
    ("Fashion & Apparel", "fashion_apparel_store.csv"),
    ("Electronics & Gadgets", "electronics_gadgets_store.csv"),
    ("Pharmacy & Healthcare", "pharmacy_healthcare_store.csv"),
    ("Bakery & Cafe", "bakery_cafe_store.csv"),
    ("Hardware & Home", "hardware_home_store.csv")
]

def test_dataset(name, filename):
    print(f"\n========================================================")
    print(f" Testing: {name} ({filename})")
    print(f"========================================================")
    
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  ❌ ERROR: File not found: {filepath}")
        return False

    # 1. Load CSV
    df = pd.read_csv(filepath)
    print(f"  [1/4] CSV Read: {len(df):,} rows, {len(df.columns)} columns")
    
    required_cols = ["Date", "Store ID", "Product ID", "Category", "Inventory Level", "Units Sold", "Demand Forecast", "Price", "Discount"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"  ❌ Missing required columns: {missing}")
        return False
    print(f"  [2/4] Schema Validation: All required columns present ✅")

    # 2. DuckDB Analytics Engine Ingestion Test
    con = duckdb.connect()
    con.register("raw_data", df)
    
    # Test Sales Overview Query
    sales_res = con.execute("""
        SELECT 
            COUNT(DISTINCT "Store ID") AS store_count,
            COUNT(DISTINCT "Category") AS category_count,
            SUM("Units Sold" * "Price" * (1 - "Discount" / 100.0)) AS total_revenue,
            SUM("Units Sold") AS total_units,
            AVG("Units Sold" * 1.0 / NULLIF("Units Sold" + GREATEST(0, "Units Sold" - "Inventory Level"), 0)) AS avg_fulfillment
        FROM raw_data
    """).fetchone()

    stores, cats, rev, units, fulf = sales_res
    print(f"  [3/4] Sales Analytics Query: {stores} Stores, {cats} Categories")
    print(f"        Total Revenue: ${rev:,.2f} | Units: {units:,} | Fulfillment: {fulf:.1%}")

    # Test Stock Alerts Query
    alert_res = con.execute("""
        WITH daily_avg AS (
            SELECT "Product ID", "Store ID", AVG("Units Sold") AS avg_daily_sales, AVG("Inventory Level") AS avg_inv
            FROM raw_data
            GROUP BY 1, 2
        )
        SELECT 
            COUNT(*) AS total_skus,
            COUNT(CASE WHEN avg_inv / NULLIF(avg_daily_sales, 0) < 30 THEN 1 END) AS understock,
            COUNT(CASE WHEN avg_inv / NULLIF(avg_daily_sales, 0) > 120 THEN 1 END) AS overstock
        FROM daily_avg
    """).fetchone()

    total_skus, under, over = alert_res
    print(f"  [4/4] Stock Alerts Query: {total_skus} SKUs (Understock: {under}, Overstock: {over}) ✅")
    con.close()
    return True

if __name__ == "__main__":
    results = {}
    for name, fname in datasets:
        success = test_dataset(name, fname)
        results[name] = "PASSED ✅" if success else "FAILED ❌"

    print("\n" + "=" * 56)
    print("  SUMMARY TEST RESULTS FOR ALL STORE CATEGORIES")
    print("=" * 56)
    for name, status in results.items():
        print(f"  {name:30} : {status}")
    print("=" * 56)
