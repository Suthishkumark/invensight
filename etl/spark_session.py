"""
Spark Session factory for InvenSight ETL pipeline.
Creates and configures a local PySpark session.
"""

from pyspark.sql import SparkSession


def get_spark_session(
    app_name: str = "InvenSight-ETL",
    master: str = "local[*]",
    log_level: str = "WARN",
) -> SparkSession:
    """
    Create or retrieve an existing SparkSession configured for local ETL workloads.

    Parameters
    ----------
    app_name : str, optional
        Application name displayed in Spark UI (default: "InvenSight-ETL").
    master : str, optional
        Spark master URL (default: "local[*]").
    log_level : str, optional
        Log level for Spark context (default: "WARN").

    Returns
    -------
    SparkSession
    """
    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.default.parallelism", "4")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.ui.showConsoleProgress", "false")
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel(log_level)
    return spark
