"""
Transform phase -- PySpark equivalents of all 5 dbt models.
Config-driven: uses column mapping from data_config.yaml to rename columns.
Optional columns get sensible defaults if not present in the source data.

Model dependency graph:
    raw_sales
       +-- stg_sales
              +-- dim_product
              +-- fct_sales
              |      +-- mart_stock_alerts  (+ dim_product)
              |      +-- mart_demand_forecast
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from typing import Optional


def _get_col_or_default(df: DataFrame, csv_col: Optional[str], default_value, cast_type: str = None):
    """
    Return a Column expression: either the mapped CSV column or a literal default.
    """
    if csv_col and csv_col in df.columns:
        c = F.col(f"`{csv_col}`")
        if cast_type:
            c = c.cast(cast_type)
        return c
    else:
        return F.lit(default_value)


# ---------------------------------------------------------------------------
#  1. stg_sales  (replaces dbt staging/stg_sales.sql)
# ---------------------------------------------------------------------------
def build_stg_sales(raw_df: DataFrame, config: dict) -> DataFrame:
    """
    Clean and rename raw columns to snake_case using config mapping.
    Fills defaults for optional columns not present in the source data.
    Filters out rows with negative units_sold, demand_forecast, or inventory_level.
    """
    col_map = config.get("columns", {})

    def _mapped(field: str) -> Optional[str]:
        val = col_map.get(field)
        if val and str(val).strip().lower() not in ("", "null", "none"):
            return str(val)
        return None

    stg = raw_df.select(
        _get_col_or_default(raw_df, _mapped("date"),               None,      "date").alias("sale_date"),
        _get_col_or_default(raw_df, _mapped("store_id"),           "UNKNOWN", "string").alias("store_id"),
        _get_col_or_default(raw_df, _mapped("product_id"),         "UNKNOWN", "string").alias("product_id"),
        _get_col_or_default(raw_df, _mapped("category"),           "General", "string").alias("category"),
        _get_col_or_default(raw_df, _mapped("region"),             "Default", "string").alias("region"),
        _get_col_or_default(raw_df, _mapped("inventory_level"),    0,         "int").alias("inventory_level"),
        _get_col_or_default(raw_df, _mapped("units_sold"),         0,         "int").alias("units_sold"),
        _get_col_or_default(raw_df, _mapped("demand_forecast"),    0.0,       "double").alias("demand_forecast"),
        _get_col_or_default(raw_df, _mapped("price"),              0.0,       "double").alias("price"),
        _get_col_or_default(raw_df, _mapped("discount"),           0,         "int").alias("discount_percentage"),
        _get_col_or_default(raw_df, _mapped("weather_condition"),  "Unknown", "string").alias("weather_condition"),
        _get_col_or_default(raw_df, _mapped("holiday_promotion"),  0,         "int").alias("holiday_promotion"),
        _get_col_or_default(raw_df, _mapped("seasonality"),        "Unknown", "string").alias("seasonality"),
        _get_col_or_default(raw_df, _mapped("competitor_pricing"), 0.0,       "double").alias("competitor_pricing"),
    )

    # If competitor_pricing was not mapped, default it to the product price
    if not _mapped("competitor_pricing"):
        stg = stg.withColumn("competitor_pricing", F.col("price"))

    # Basic cleaning: remove negative values (mirrors dbt WHERE clause)
    stg = stg.filter(
        (F.col("units_sold") >= 0)
        & (F.col("demand_forecast") >= 0)
        & (F.col("inventory_level") >= 0)
    )

    return stg


# ---------------------------------------------------------------------------
#  2. dim_product  (replaces dbt marts/dim_product.sql)
# ---------------------------------------------------------------------------
def build_dim_product(stg_df: DataFrame) -> DataFrame:
    """
    Build product dimension: distinct products with category, price,
    and competitor_pricing.
    """
    dim = (
        stg_df
        .select("product_id", "category", "price", "competitor_pricing")
        .dropDuplicates()
    )
    return dim


# ---------------------------------------------------------------------------
#  3. fct_sales  (replaces dbt marts/fct_sales.sql)
# ---------------------------------------------------------------------------
def build_fct_sales(stg_df: DataFrame) -> DataFrame:
    """
    Build fact table with calculated revenue, stock_gap, and fulfillment_rate.
    """
    fct = (
        stg_df
        .withColumn(
            "revenue",
            F.round(
                F.col("units_sold")
                * F.col("price")
                * (1 - F.col("discount_percentage") / 100.0),
                2,
            ),
        )
        .withColumn(
            "stock_gap",
            F.col("inventory_level") - F.col("demand_forecast"),
        )
        .withColumn(
            "fulfillment_rate",
            F.when(F.col("demand_forecast") == 0, 0.0).otherwise(
                F.least(
                    (F.col("units_sold").cast("double") / F.col("demand_forecast")),
                    F.lit(1.0),
                )
            ),
        )
        .select(
            "sale_date",
            "store_id",
            "product_id",
            "units_sold",
            "price",
            "discount_percentage",
            "revenue",
            "inventory_level",
            "demand_forecast",
            "stock_gap",
            "fulfillment_rate",
            "weather_condition",
            "holiday_promotion",
            "seasonality",
        )
    )
    return fct


# ---------------------------------------------------------------------------
#  4. mart_stock_alerts  (replaces dbt marts/mart_stock_alerts.sql)
# ---------------------------------------------------------------------------
def build_mart_stock_alerts(fct_df: DataFrame, dim_df: DataFrame) -> DataFrame:
    """
    Join fact + dimension, aggregate per store x product, compute days_of_stock,
    and assign alert status (UNDERSTOCK / OVERSTOCK / HEALTHY / UNKNOWN).
    """
    # -- Base aggregation --
    base = (
        fct_df
        .join(dim_df.select("product_id", "category"), on="product_id", how="left")
        .groupBy("store_id", "product_id", "category")
        .agg(
            F.avg("inventory_level").alias("avg_inventory"),
            F.avg("units_sold").alias("avg_units_sold"),
            F.avg("demand_forecast").alias("avg_demand_forecast"),
            F.avg("fulfillment_rate").alias("avg_fulfillment"),
            F.sum("revenue").alias("total_revenue"),
            F.count("*").alias("records"),
        )
    )

    # -- Days of stock --
    with_days = base.withColumn(
        "days_of_stock",
        F.when(
            (F.col("avg_units_sold") / 30.0) <= 0, F.lit(None)
        ).otherwise(
            F.round(F.col("avg_inventory") / (F.col("avg_units_sold") / 30.0), 1)
        ),
    )

    # -- Alert status + urgency --
    with_alerts = (
        with_days
        .withColumn(
            "alert_status",
            F.when(F.col("days_of_stock").isNull(), "UNKNOWN")
            .when(F.col("days_of_stock") < 30, "UNDERSTOCK")
            .when(F.col("days_of_stock") > 120, "OVERSTOCK")
            .otherwise("HEALTHY"),
        )
        .withColumn(
            "urgency_score",
            F.when(F.col("days_of_stock") < 30, F.round(30 - F.col("days_of_stock"), 1)).otherwise(
                F.lit(0.0)
            ),
        )
        .orderBy(F.desc("urgency_score"), F.asc_nulls_last("days_of_stock"))
    )
    return with_alerts


# ---------------------------------------------------------------------------
#  5. mart_demand_forecast  (replaces dbt marts/mart_demand_forecast.sql)
# ---------------------------------------------------------------------------
def build_mart_demand_forecast(fct_df: DataFrame) -> DataFrame:
    """
    Aggregate to daily level: actual vs forecasted units, forecast error,
    avg fulfillment. Ordered by sale_date.
    """
    daily = (
        fct_df
        .groupBy("sale_date", "seasonality", "weather_condition", "holiday_promotion")
        .agg(
            F.sum("units_sold").alias("actual_units"),
            F.sum("demand_forecast").alias("forecasted_units"),
            F.avg("fulfillment_rate").alias("avg_fulfillment"),
            F.countDistinct(F.concat("store_id", "product_id")).alias("product_store_count"),
        )
        .withColumn(
            "forecast_error",
            F.round(F.col("actual_units") - F.col("forecasted_units"), 0),
        )
        .orderBy("sale_date")
    )
    return daily
