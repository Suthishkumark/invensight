import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DBT_DIR  = os.path.join(BASE_DIR, 'dbt_retail')

def run_extraction():
    print("[1/2] Extraction Phase — loading CSV into DuckDB...")
    script = os.path.join(BASE_DIR, 'Scripts', 'extract_load.py')
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print("  ERROR: Extraction failed.")
        sys.exit(1)
    print("  Extraction complete.\n")

def run_dbt():
    print("[2/2] dbt Modeling Phase — building all models...")
    result = subprocess.run(
        ["dbt", "build", "--profiles-dir", "."],
        cwd=DBT_DIR, shell=True
    )
    if result.returncode != 0:
        print("  ERROR: dbt build failed.")
        sys.exit(1)
    print("  dbt models built successfully.\n")

def run_pyspark_etl():
    print("[1/1] PySpark ETL — running full Extract → Transform → Load...")
    result = subprocess.run(
        [sys.executable, "-m", "etl.pipeline"],
        cwd=BASE_DIR
    )
    if result.returncode != 0:
        print("  ERROR: PySpark ETL failed.")
        sys.exit(1)

if __name__ == '__main__':
    # Parse optional --mode flag: "dbt" (default) or "pyspark"
    mode = "pyspark"  # default to pyspark
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1].lower()

    if mode == "dbt":
        print("=" * 60)
        print("  InvenSight Data Pipeline  (dbt mode)")
        print("=" * 60)
        run_extraction()
        run_dbt()
        print("=" * 60)
        print("  Pipeline complete! Run the dashboard with:")
        print("  streamlit run Dashboard\\app.py")
        print("=" * 60)
    elif mode == "pyspark":
        print("=" * 60)
        print("  InvenSight Data Pipeline  (PySpark mode)")
        print("=" * 60)
        run_pyspark_etl()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python Scripts/run_pipeline.py [--mode dbt|pyspark]")
        sys.exit(1)
