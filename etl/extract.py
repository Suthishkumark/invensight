"""
Extract phase -- reads the raw CSV into a Spark DataFrame with config-driven schema.
Supports any CSV format via column mapping from data_config.yaml.
"""

import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType,
)
from pyspark.sql.functions import to_date, col, lit

# Type hints for each InvenSight field
_FIELD_TYPES = {
    "date":               StringType(),   # parsed to DateType after read
    "store_id":           StringType(),
    "product_id":         StringType(),
    "category":           StringType(),
    "region":             StringType(),
    "inventory_level":    IntegerType(),
    "units_sold":         IntegerType(),
    "units_ordered":      IntegerType(),
    "demand_forecast":    DoubleType(),
    "price":              DoubleType(),
    "discount":           IntegerType(),
    "weather_condition":  StringType(),
    "holiday_promotion":  IntegerType(),
    "competitor_pricing": DoubleType(),
    "seasonality":        StringType(),
}


def extract_raw_sales(spark: SparkSession, base_dir: str, config: dict) -> DataFrame:
    """
    Read the source CSV and return a Spark DataFrame.
    Uses column mappings from config to build the schema dynamically.

    Parameters
    ----------
    spark : SparkSession
    base_dir : str
        Root directory of the InvenSight project.
    config : dict
        Configuration loaded from data_config.yaml.

    Returns
    -------
    DataFrame with columns named as the user's CSV headers + Date parsed.
    """
    source = config.get("source", {})
    csv_file = source.get("file", "Data/retail_store.csv")
    date_format = source.get("date_format", "dd-MM-yyyy")

    # Resolve CSV path (relative to base_dir or absolute)
    if os.path.isabs(csv_file):
        csv_path = csv_file
    else:
        csv_path = os.path.join(base_dir, csv_file)

    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Source CSV not found: {csv_path}")

    # Build schema from column mapping
    col_mapping = config.get("columns", {})
    mapped_csv_columns = {
        field: col_mapping[field]
        for field in col_mapping
        if col_mapping[field] and str(col_mapping[field]).strip().lower() not in ("", "null", "none")
    }

    # Read with header inference (we'll select/rename later)
    raw_df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(csv_path)
    )

    # Get actual CSV headers for validation
    csv_headers = set(raw_df.columns)

    # Validate that mapped columns exist in the CSV
    missing = []
    for field, csv_col in mapped_csv_columns.items():
        if csv_col not in csv_headers:
            missing.append(f"  '{csv_col}' (mapped to '{field}') not found in CSV")
    if missing:
        available = ", ".join(sorted(csv_headers))
        raise ValueError(
            f"Column mapping errors:\n"
            + "\n".join(missing)
            + f"\n\nAvailable CSV columns: {available}"
        )

    # Parse date column
    date_csv_col = mapped_csv_columns.get("date")
    if date_csv_col:
        raw_df = raw_df.withColumn(
            date_csv_col,
            to_date(col(date_csv_col).cast("string"), date_format)
        )

    return raw_df
