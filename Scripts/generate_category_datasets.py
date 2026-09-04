"""
Generate realistic, high-quality Kaggle-format retail datasets for all store categories.
Saves CSV files to Data/ directory.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
os.makedirs(DATA_DIR, exist_ok=True)

# Common dates (365 days)
start_date = datetime(2023, 1, 1)
dates = [(start_date + timedelta(days=i)).strftime("%d-%m-%Y") for i in range(365)]
regions = ["North", "South", "East", "West", "Central"]
weathers = ["Sunny", "Rainy", "Cloudy", "Snowy"]
seasons = ["Spring", "Summer", "Autumn", "Winter"]

# Store Category Definitions
CATEGORIES_CONFIG = {
    "supermarket_grocery_store.csv": {
        "stores": ["Store_Downtown", "Store_Suburbs", "Store_Uptown", "Store_Metro", "Store_Airport"],
        "categories": {
            "Fresh Produce": (1.50, 8.00, 50, 450, 40, 200),
            "Dairy & Eggs": (2.00, 12.00, 40, 300, 30, 150),
            "Meat & Seafood": (5.00, 35.00, 20, 180, 15, 90),
            "Bakery & Snacks": (1.80, 10.00, 50, 350, 35, 160),
            "Beverages": (1.20, 15.00, 60, 500, 40, 250),
            "Frozen Foods": (3.00, 22.00, 30, 250, 20, 120),
            "Household Essentials": (4.00, 28.00, 25, 200, 15, 100)
        },
        "num_products": 25,
        "rows": 15000
    },
    "fashion_apparel_store.csv": {
        "stores": ["Outlet_Mall", "Flagship_City", "Boutique_West", "Plaza_Fashion", "Galleria_North"],
        "categories": {
            "Womenswear": (19.99, 149.99, 15, 120, 5, 45),
            "Menswear": (24.99, 169.99, 15, 110, 5, 40),
            "Footwear": (39.99, 199.99, 10, 80, 4, 30),
            "Activewear": (29.99, 119.99, 20, 140, 8, 50),
            "Accessories": (9.99, 69.99, 30, 220, 10, 70),
            "Winterwear & Jackets": (49.99, 299.99, 10, 75, 3, 25)
        },
        "num_products": 20,
        "rows": 12000
    },
    "electronics_gadgets_store.csv": {
        "stores": ["Tech_Hub_Central", "Express_Cyber", "Digital_Mall", "Smart_Center", "Gizmo_Avenue"],
        "categories": {
            "Smartphones": (199.00, 1199.00, 8, 50, 2, 20),
            "Laptops & Computers": (399.00, 2299.00, 5, 35, 1, 15),
            "Audio & Headphones": (29.99, 349.99, 25, 180, 8, 60),
            "Gaming & Consoles": (49.99, 599.99, 10, 70, 3, 25),
            "Wearables & Smartwatches": (79.99, 449.99, 15, 90, 5, 35),
            "Accessories & Cables": (9.99, 59.99, 50, 400, 20, 150)
        },
        "num_products": 20,
        "rows": 12000
    },
    "pharmacy_healthcare_store.csv": {
        "stores": ["Pharma_Central", "Care_Clinics", "Health_Point_East", "Wellness_Avenue", "Medi_Express"],
        "categories": {
            "Prescription Medicines": (8.50, 120.00, 30, 250, 15, 110),
            "OTC Medicines": (3.50, 25.00, 50, 400, 25, 160),
            "Vitamins & Supplements": (9.99, 49.99, 35, 220, 12, 85),
            "Personal Care": (2.99, 22.99, 40, 300, 18, 120),
            "Medical Devices & First Aid": (12.00, 180.00, 15, 90, 4, 30)
        },
        "num_products": 20,
        "rows": 12000
    },
    "bakery_cafe_store.csv": {
        "stores": ["Artisan_Oven_Downtown", "Morning_Crust_Uptown", "Sweet_Slice_Mall", "Cafe_Branch_West", "Corner_Bakeshop"],
        "categories": {
            "Artisan Breads": (2.50, 8.50, 40, 300, 30, 220),
            "Pastries & Croissants": (2.00, 6.50, 50, 400, 35, 280),
            "Cakes & Desserts": (15.00, 65.00, 10, 60, 5, 35),
            "Hot & Cold Beverages": (1.80, 6.50, 80, 600, 60, 450),
            "Savoury Pies & Quiches": (3.50, 12.00, 30, 200, 20, 140)
        },
        "num_products": 18,
        "rows": 10000
    },
    "hardware_home_store.csv": {
        "stores": ["BuildPro_Depot_North", "Hardware_Hub_South", "Timber_Craft_East", "FixIt_MegaStore", "Craftsman_Plaza"],
        "categories": {
            "Power Tools": (49.99, 399.99, 10, 60, 2, 22),
            "Hand Tools": (8.99, 79.99, 30, 220, 8, 65),
            "Plumbing & Fixtures": (4.50, 150.00, 25, 180, 6, 50),
            "Electrical & Lighting": (3.99, 120.00, 35, 250, 10, 80),
            "Paints & Finishes": (12.99, 85.00, 20, 150, 5, 45),
            "Building Materials": (5.00, 95.00, 40, 350, 12, 110)
        },
        "num_products": 20,
        "rows": 12000
    }
}

def generate_dataset(filename, config):
    print(f"Generating {filename}...")
    records = []
    stores = config["stores"]
    cat_defs = config["categories"]
    cat_names = list(cat_defs.keys())
    
    # Generate products
    products = []
    for i in range(1, config["num_products"] + 1):
        cat = random.choice(cat_names)
        p_id = f"SKU{i:04d}"
        min_p, max_p, min_inv, max_inv, min_u, max_u = cat_defs[cat]
        base_price = round(random.uniform(min_p, max_p), 2)
        products.append({
            "product_id": p_id,
            "category": cat,
            "base_price": base_price,
            "min_inv": min_inv,
            "max_inv": max_inv,
            "min_u": min_u,
            "max_u": max_u
        })

    target_rows = config["rows"]
    rows_generated = 0

    while rows_generated < target_rows:
        date = random.choice(dates)
        store = random.choice(stores)
        prod = random.choice(products)
        region = random.choice(regions)
        weather = random.choice(weathers)
        season = random.choice(seasons)
        is_holiday = 1 if random.random() < 0.12 else 0

        # Inventory and sales simulation
        inv = random.randint(prod["min_inv"], prod["max_inv"])
        
        # Holiday/weather multiplier
        mult = 1.0
        if is_holiday: mult *= 1.35
        if weather == "Rainy" and prod["category"] in ["Fresh Produce", "Hot & Cold Beverages", "Winterwear & Jackets"]:
            mult *= 1.25
        elif weather == "Sunny" and prod["category"] in ["Beverages", "Activewear", "Footwear"]:
            mult *= 1.30

        units_sold = int(random.randint(prod["min_u"], prod["max_u"]) * mult)
        units_sold = min(units_sold, inv + 20)  # can have stockout gap
        units_ordered = int(units_sold * random.uniform(0.8, 1.3))
        demand_forecast = round(units_sold * random.uniform(0.85, 1.15), 2)

        # Price & discounts
        discount = random.choice([0, 5, 10, 15, 20, 25]) if is_holiday or random.random() < 0.25 else 0
        price = prod["base_price"]
        comp_price = round(price * random.uniform(0.92, 1.08), 2)

        records.append({
            "Date": date,
            "Store ID": store,
            "Product ID": prod["product_id"],
            "Category": prod["category"],
            "Region": region,
            "Inventory Level": inv,
            "Units Sold": units_sold,
            "Units Ordered": units_ordered,
            "Demand Forecast": demand_forecast,
            "Price": price,
            "Discount": discount,
            "Weather Condition": weather,
            "Holiday/Promotion": is_holiday,
            "Competitor Pricing": comp_price,
            "Seasonality": season
        })
        rows_generated += 1

    df = pd.DataFrame(records)
    out_path = os.path.join(DATA_DIR, filename)
    df.to_csv(out_path, index=False)
    print(f"  -> Saved {len(df):,} rows to {out_path}")

if __name__ == "__main__":
    for fname, cfg in CATEGORIES_CONFIG.items():
        generate_dataset(fname, cfg)
    print("\nAll 6 store category datasets successfully created in Data/!")
