import duckdb
import os

def load_data():
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'Data', 'retail.duckdb')
    csv_path = os.path.join(base_dir, 'Data', 'retail_store.csv')
    
    # Ensure Data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"Connecting to DuckDB at: {db_path}")
    conn = duckdb.connect(db_path)
    
    print("Creating 'raw' schema...")
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    
    print(f"Loading data from {csv_path} into raw.sales...")
    # DuckDB's read_csv_auto is incredibly fast and infers types automatically
    conn.execute(f"""
        CREATE OR REPLACE TABLE raw.sales AS 
        SELECT * FROM read_csv_auto('{csv_path}');
    """)
    
    count = conn.execute("SELECT COUNT(*) FROM raw.sales").fetchone()[0]
    print(f"Successfully loaded {count:,} rows into raw.sales")
    conn.close()

if __name__ == '__main__':
    load_data()
