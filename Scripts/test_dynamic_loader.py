import os
import duckdb
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "Data", "supermarket_grocery_store.csv")

df_raw = pd.read_csv(csv_path)
con = duckdb.connect()
con.register("raw_csv", df_raw)

res = con.execute("""
    WITH cleaned AS (
        SELECT 
            CAST(strptime(CAST("Date" AS VARCHAR), '%d-%m-%Y') AS DATE) AS sale_date,
            CAST("Store ID" AS VARCHAR) AS store_id,
            CAST("Product ID" AS VARCHAR) AS product_id,
            CAST("Category" AS VARCHAR) AS category,
            CAST("Inventory Level" AS INTEGER) AS inventory_level,
            CAST("Units Sold" AS INTEGER) AS units_sold,
            CAST("Price" AS DOUBLE) AS price,
            CAST(COALESCE("Discount", 0) AS DOUBLE) AS discount
        FROM raw_csv
    ),
    fct AS (
        SELECT 
            sale_date, store_id, product_id, category,
            (units_sold * price * (1.0 - discount / 100.0)) AS revenue,
            units_sold,
            GREATEST(0, units_sold - inventory_level) AS stock_gap,
            (units_sold * 1.0 / NULLIF(units_sold + GREATEST(0, units_sold - inventory_level), 0)) AS fulfillment_rate
        FROM cleaned
    )
    SELECT 
        COUNT(DISTINCT store_id) AS stores,
        COUNT(DISTINCT category) AS cats,
        SUM(revenue) AS total_revenue,
        SUM(units_sold) AS total_units,
        AVG(COALESCE(fulfillment_rate, 1.0)) AS avg_fulfillment
    FROM fct
""").fetchone()

print("Grocery Query Output:", res)
