"""
PySpark Big Data Processing Module.
Provides distributed data operations using Apache Spark.
Includes automated Java/Spark environment diagnostics, resilient SparkSession creation,
DataFrame transformations, deduplication, Spark SQL execution, and safe conversion to Pandas.
"""

import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from config import REQUIRED_COLUMNS, SPARK_CONFIG, STANDARD_CATEGORY_MAP


import glob
import os

def _ensure_java_env():
    """
    Auto-detects OpenJDK/Java on Windows and sets JAVA_HOME and PATH
    in the current process if not already available in PATH.
    """
    if shutil.which("java"):
        return

    # Check JAVA_HOME environment variable
    java_home = os.environ.get("JAVA_HOME")
    if java_home and os.path.exists(os.path.join(java_home, "bin", "java.exe")):
        os.environ["PATH"] = os.path.join(java_home, "bin") + os.pathsep + os.environ.get("PATH", "")
        return

    # Auto-discover common Windows OpenJDK installation directories
    candidate_patterns = [
        r"C:\Program Files\Microsoft\jdk*",
        r"C:\Program Files\Eclipse Adoptium\jdk*",
        r"C:\Program Files\Java\jdk*",
        r"C:\Program Files (x86)\Java\jdk*",
    ]
    for pattern in candidate_patterns:
        matches = sorted(glob.glob(pattern), reverse=True)
        for jdk_path in matches:
            java_exe = os.path.join(jdk_path, "bin", "java.exe")
            if os.path.exists(java_exe):
                os.environ["JAVA_HOME"] = jdk_path
                os.environ["PATH"] = os.path.join(jdk_path, "bin") + os.pathsep + os.environ.get("PATH", "")
                return


def check_spark_environment() -> Dict[str, Any]:
    """
    Checks whether Java and PySpark runtimes are properly installed and accessible.
    Provides clear diagnostics and beginner-friendly instructions if missing.

    Returns:
        dict: Diagnostics status including availability, java version, and setup guide.
    """
    # Attempt auto-detection in case terminal has not refreshed PATH
    _ensure_java_env()

    status = {
        "pyspark_installed": False,
        "java_installed": False,
        "java_version": None,
        "is_ready": False,
        "message": "",
        "setup_guide": "",
    }

    # Check PySpark package
    try:
        import pyspark  # noqa: F401
        status["pyspark_installed"] = True
    except ImportError:
        status["pyspark_installed"] = False
        status["message"] = "PySpark package is not installed."
        status["setup_guide"] = "Run: pip install pyspark"
        return status

    # Check Java executable
    java_bin = shutil.which("java")
    if not java_bin:
        status["java_installed"] = False
        status["message"] = (
            "Java Runtime (JRE/JDK) was not found in your system PATH. "
            "Apache Spark is built on Scala/JVM and requires Java 8, 11, or 17 to execute distributed jobs."
        )
        status["setup_guide"] = (
            "To enable PySpark mode on Windows:\n"
            "1. Install OpenJDK via Windows PowerShell:\n"
            "   winget install Microsoft.OpenJDK.17\n"
            "2. Ensure JAVA_HOME is set in your environment variables.\n"
            "3. Restart your terminal."
        )
        return status

    # Retrieve Java version
    try:
        res = subprocess.run(
            [java_bin, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
        )
        status["java_installed"] = True
        first_line = res.stdout.splitlines()[0] if res.stdout else "Java detected"
        status["java_version"] = first_line
        status["is_ready"] = True
        status["message"] = f"PySpark and Java runtime are ready ({first_line})."
    except Exception as e:
        status["java_installed"] = False
        status["message"] = f"Java executable found but failed to run: {e}"

    return status


def get_spark_session(app_name: Optional[str] = None):
    """
    Initializes or retrieves an active local Apache SparkSession.
    Configures low shuffle partitions and memory caps suitable for personal laptops.
    """
    env = check_spark_environment()
    if not env["is_ready"]:
        raise RuntimeError(
            f"Cannot initialize SparkSession: {env['message']}\n\n{env['setup_guide']}"
        )

    from pyspark.sql import SparkSession

    name = app_name or SPARK_CONFIG["app_name"]
    builder = (
        SparkSession.builder.appName(name)
        .master(SPARK_CONFIG["master"])
        .config("spark.driver.memory", SPARK_CONFIG["driver_memory"])
        .config("spark.sql.shuffle.partitions", SPARK_CONFIG["sql_shuffle_partitions"])
        .config("spark.ui.enabled", "false")  # Avoid port conflicts on local laptops
    )

    spark = builder.getOrCreate()
    return spark


def process_with_pyspark(
    spark,
    csv_path: str,
    category_map: Optional[Dict[int, str]] = None,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Executes a distributed data pipeline on the YouTube trending dataset using PySpark:
    1. Distributed CSV ingestion with header and multiline support.
    2. Column validation against the required schema.
    3. Type casting to LongType and DoubleType.
    4. Distributed deduplication with dropDuplicates(['video_id', 'trending_date']).
    5. Clean ratio calculation with when/otherwise conditional expressions.
    6. Registers a temporary SQL view ('trending_videos') for Spark SQL querying.

    Returns:
        tuple: (spark_df, execution_metrics)
    """
    import time
    from pyspark.sql import functions as F
    from pyspark.sql.types import IntegerType, LongType, StringType

    start_time = time.time()

    # 1. Read CSV into Spark DataFrame
    raw_df = (
        spark.read.option("header", "true")
        .option("multiLine", "true")
        .option("escape", '"')
        .csv(str(csv_path))
    )

    raw_columns = raw_df.columns
    missing = [c for c in REQUIRED_COLUMNS if c not in raw_columns]
    if missing:
        raise ValueError(f"Spark schema validation failed: Missing columns {missing}")

    raw_count = raw_df.count()

    # 2. Select & Type Cast
    df = raw_df.withColumn("views", F.col("views").cast(LongType()))

    # Optional columns casting
    if "likes" in raw_columns:
        df = df.withColumn("likes", F.coalesce(F.col("likes").cast(LongType()), F.lit(0)))
    else:
        df = df.withColumn("likes", F.lit(0).cast(LongType()))

    if "dislikes" in raw_columns:
        df = df.withColumn("dislikes", F.coalesce(F.col("dislikes").cast(LongType()), F.lit(0)))
    else:
        df = df.withColumn("dislikes", F.lit(0).cast(LongType()))

    if "comment_count" in raw_columns:
        df = df.withColumn(
            "comment_count", F.coalesce(F.col("comment_count").cast(LongType()), F.lit(0))
        )
    else:
        df = df.withColumn("comment_count", F.lit(0).cast(LongType()))

    if "category_id" in raw_columns:
        df = df.withColumn(
            "category_id", F.coalesce(F.col("category_id").cast(IntegerType()), F.lit(0))
        )

    # 3. Filter Invalid Views
    df = df.filter(F.col("views").isNotNull() & (F.col("views") >= 0))

    # 4. Distributed Deduplication
    if "trending_date" in raw_columns:
        df = df.dropDuplicates(["video_id", "trending_date"])
    else:
        df = df.dropDuplicates(["video_id"])

    # 5. Engagement Metrics (Safe Division)
    df = df.withColumn(
        "like_view_ratio",
        F.when(F.col("views") > 0, (F.col("likes") / F.col("views")) * 100).otherwise(0.0),
    ).withColumn(
        "comment_view_ratio",
        F.when(F.col("views") > 0, (F.col("comment_count") / F.col("views")) * 100).otherwise(0.0),
    )

    # 6. Category Name Mapping via Spark Expressions
    mapping = category_map or STANDARD_CATEGORY_MAP
    # Build a Spark CASE WHEN expression for category mapping
    cat_expr = None
    for cid, cname in mapping.items():
        if cat_expr is None:
            cat_expr = F.when(F.col("category_id") == cid, F.lit(cname))
        else:
            cat_expr = cat_expr.when(F.col("category_id") == cid, F.lit(cname))

    if cat_expr is not None:
        df = df.withColumn(
            "category_name",
            cat_expr.otherwise(F.concat(F.lit("Category "), F.col("category_id").cast(StringType()))),
        )
    else:
        df = df.withColumn(
            "category_name", F.concat(F.lit("Category "), F.col("category_id").cast(StringType()))
        )

    # Cache for reuse in analytics
    df.cache()
    clean_count = df.count()

    # Register Spark SQL View
    df.createOrReplaceTempView("trending_videos")

    elapsed_time = round(time.time() - start_time, 2)

    metrics = {
        "raw_record_count": raw_count,
        "clean_record_count": clean_count,
        "records_dropped": raw_count - clean_count,
        "spark_partitions": df.rdd.getNumPartitions(),
        "spark_execution_time_seconds": elapsed_time,
        "spark_master": spark.sparkContext.master,
        "spark_version": spark.version,
    }

    return df, metrics


def run_spark_sql(spark, query: str) -> pd.DataFrame:
    """
    Executes an arbitrary Spark SQL query against the 'trending_videos' view
    and returns a pandas DataFrame.
    """
    spark_res = spark.sql(query)
    return spark_res.toPandas()


def get_spark_category_summary(spark_df) -> pd.DataFrame:
    """
    Calculates category summary using native Spark DataFrame aggregations.
    """
    from pyspark.sql import functions as F

    cat_df = (
        spark_df.groupBy("category_name")
        .agg(
            F.count("video_id").alias("trending_records"),
            F.countDistinct("video_id").alias("unique_videos"),
            F.sum("views").alias("total_views"),
            F.round(F.avg("views"), 1).alias("avg_views"),
            F.sum("likes").alias("total_likes"),
            F.sum("comment_count").alias("total_comments"),
            F.round(F.avg("like_view_ratio"), 2).alias("avg_like_ratio"),
        )
        .orderBy(F.col("total_views").desc())
    )

    return cat_df.toPandas()


def get_spark_channel_summary(spark_df, limit: int = 20) -> pd.DataFrame:
    """
    Calculates top channels using native Spark DataFrame aggregations.
    """
    from pyspark.sql import functions as F

    chan_df = (
        spark_df.groupBy("channel_title")
        .agg(
            F.count("video_id").alias("trending_records"),
            F.countDistinct("video_id").alias("unique_videos"),
            F.sum("views").alias("total_views"),
            F.round(F.avg("views"), 1).alias("avg_views_per_record"),
            F.sum("likes").alias("total_likes"),
            F.sum("comment_count").alias("total_comments"),
        )
        .orderBy(F.col("trending_records").desc())
        .limit(limit)
    )

    return chan_df.toPandas()
