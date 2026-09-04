"""
Load phase — writes transformed DataFrames to Parquet files and DuckDB tables.
"""

import os
import duckdb
from pyspark.sql import DataFrame


def _write_parquet(df: DataFrame, output_dir: str, table_name: str) -> str:
    """Write a Spark DataFrame to a single Parquet file (coalesced)."""
    parquet_dir = os.path.join(output_dir, "parquet", table_name)
    (
        df.coalesce(1)
        .write
        .mode("overwrite")
        .parquet(parquet_dir)
    )
    return parquet_dir


def _write_to_duckdb(df: DataFrame, db_path: str, schema: str, table_name: str):
    """
    Convert Spark DataFrame → Pandas → DuckDB table.
    Uses DuckDB's ability to create tables directly from Pandas DataFrames.
    """
    pdf = df.toPandas()
    conn = duckdb.connect(db_path)
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
    # Drop any existing object (view or table) to avoid type conflicts.
    # DuckDB raises an error if you DROP VIEW on a TABLE and vice versa,
    # so we attempt both and ignore errors.
    for drop_type in ("VIEW", "TABLE"):
        try:
            conn.execute(f"DROP {drop_type} IF EXISTS {schema}.{table_name};")
        except duckdb.CatalogException:
            pass
    conn.execute(f"CREATE TABLE {schema}.{table_name} AS SELECT * FROM pdf")
    row_count = conn.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}").fetchone()[0]
    conn.close()
    return row_count


def load_table(
    df: DataFrame,
    table_name: str,
    base_dir: str,
    write_parquet: bool = True,
    write_duckdb: bool = True,
    duckdb_schema: str = "analytics",
) -> dict:
    """
    Load a single transformed DataFrame to output destinations.

    Parameters
    ----------
    df : DataFrame
        Spark DataFrame to persist.
    table_name : str
        Logical table name (e.g., 'stg_sales', 'fct_sales').
    base_dir : str
        Root directory of the InvenSight project.
    write_parquet : bool
        Whether to write to Parquet files.
    write_duckdb : bool
        Whether to write to DuckDB (for dashboard compatibility).
    duckdb_schema : str
        DuckDB schema to write into (default: 'analytics').

    Returns
    -------
    dict with write results.
    """
    output_dir = os.path.join(base_dir, "Output")
    db_path = os.path.join(base_dir, "Data", "retail.duckdb")
    results = {"table": table_name}

    if write_parquet:
        parquet_path = _write_parquet(df, output_dir, table_name)
        results["parquet_path"] = parquet_path
        print(f"    [OK] Parquet  -> {parquet_path}")

    if write_duckdb:
        row_count = _write_to_duckdb(df, db_path, duckdb_schema, table_name)
        results["duckdb_rows"] = row_count
        print(f"    [OK] DuckDB   -> {duckdb_schema}.{table_name}  ({row_count:,} rows)")

    return results
