"""
InvenSight PySpark ETL Pipeline -- Main Orchestrator.

Usage:
    python -m etl.pipeline          (from project root)
    python etl/pipeline.py          (from project root)

Chains:  Extract -> Transform -> Load
Outputs: Parquet files + DuckDB analytics tables
"""

import os
import sys
import time

# Force UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure the project root is on sys.path so `etl` package is importable
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_SCRIPT_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from config.settings import load_config
from etl.spark_session import get_spark_session
from etl.extract import extract_raw_sales
from etl.transform import (
    build_stg_sales,
    build_dim_product,
    build_fct_sales,
    build_mart_stock_alerts,
    build_mart_demand_forecast,
)
from etl.load import load_table


def _banner(msg: str):
    """Print a formatted banner message."""
    width = 60
    print("\n" + "=" * width)
    print(f"  {msg}")
    print("=" * width)


def run_pipeline(base_dir: str | None = None):
    """
    Execute the full ETL pipeline.

    Parameters
    ----------
    base_dir : str, optional
        Project root directory. Auto-detected if not provided.
    """
    if base_dir is None:
        base_dir = _BASE_DIR

    pipeline_start = time.time()

    _banner("InvenSight -- PySpark ETL Pipeline")

    config = load_config(base_dir)

    # -- Step 1: Spark Session -------------------------------------------------
    print("\n[1/4] Initializing Spark session...")
    t0 = time.time()
    spark = get_spark_session()
    print(f"  [OK] Spark session ready  ({time.time() - t0:.1f}s)")

    # -- Step 2: Extract -------------------------------------------------------
    print("\n[2/4] EXTRACT -- Reading raw CSV data...")
    t0 = time.time()
    raw_df = extract_raw_sales(spark, base_dir, config)
    raw_count = raw_df.count()
    source_file = config.get("source", {}).get("file", "retail_store.csv")
    print(f"  [OK] Loaded {raw_count:,} rows from {os.path.basename(source_file)}  ({time.time() - t0:.1f}s)")

    # -- Step 3: Transform -----------------------------------------------------
    print("\n[3/4] TRANSFORM -- Building data models...")
    t0 = time.time()

    print("  -> stg_sales (staging: clean + rename)")
    stg_df = build_stg_sales(raw_df, config)
    stg_df.cache()  # Cache because multiple downstream models read from it
    stg_count = stg_df.count()
    print(f"    {stg_count:,} rows after cleaning")

    print("  -> dim_product (dimension: product catalog)")
    dim_df = build_dim_product(stg_df)

    print("  -> fct_sales (fact: revenue, stock_gap, fulfillment)")
    fct_df = build_fct_sales(stg_df)
    fct_df.cache()  # Cache because stock_alerts and demand_forecast both read from it

    print("  -> mart_stock_alerts (UNDERSTOCK / OVERSTOCK / HEALTHY)")
    alerts_df = build_mart_stock_alerts(fct_df, dim_df)

    print("  -> mart_demand_forecast (actual vs forecast trend)")
    forecast_df = build_mart_demand_forecast(fct_df)

    print(f"  [OK] All 5 models built  ({time.time() - t0:.1f}s)")

    # -- Step 4: Load ----------------------------------------------------------
    print("\n[4/4] LOAD -- Writing to Parquet + DuckDB...")
    t0 = time.time()

    models = [
        ("stg_sales",            stg_df),
        ("dim_product",          dim_df),
        ("fct_sales",            fct_df),
        ("mart_stock_alerts",    alerts_df),
        ("mart_demand_forecast", forecast_df),
    ]

    for table_name, df in models:
        print(f"\n  Loading {table_name}...")
        load_table(df, table_name, base_dir)

    print(f"\n  [OK] All tables loaded  ({time.time() - t0:.1f}s)")

    # -- Cleanup ---------------------------------------------------------------
    stg_df.unpersist()
    fct_df.unpersist()
    spark.stop()

    elapsed = time.time() - pipeline_start
    _banner(f"Pipeline complete!  Total time: {elapsed:.1f}s")
    print("\n  Launch the dashboard with:")
    print("  streamlit run Dashboard\\app.py\n")


if __name__ == "__main__":
    run_pipeline()
