"""
Standalone PySpark Distributed Job Execution Script.
Allows running batch PySpark analytics directly from the terminal.
Usage:
    python run_spark.py
    python run_spark.py --input data/INvideos.csv
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DEFAULT_CSV_PATH
from src.data_loader import load_category_mappings
from src.pyspark_processor import (
    check_spark_environment,
    get_spark_category_summary,
    get_spark_channel_summary,
    get_spark_session,
    process_with_pyspark,
    run_spark_sql,
)


def main():
    parser = argparse.ArgumentParser(description="Run PySpark Batch Job on YouTube Trending Data")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_CSV_PATH),
        help=f"Path to YouTube CSV dataset (default: {DEFAULT_CSV_PATH})",
    )
    args = parser.parse_args()

    input_file = Path(args.input)
    print("=" * 70)
    print("  ▶ YOUTUBE TRENDING ANALYTICS - PYSPARK BATCH JOB")
    print("=" * 70)

    # 1. Environment Check
    print("\n[1/5] Checking PySpark & Java Runtime Environment...")
    env_status = check_spark_environment()
    if not env_status["is_ready"]:
        print(f"❌ Error: {env_status['message']}")
        print(f"\nSetup Guide:\n{env_status['setup_guide']}")
        sys.exit(1)

    print(f"✓ {env_status['message']}")

    # 2. Check Input File
    print(f"\n[2/5] Locating input dataset at: {input_file.resolve()}...")
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        print("Please place INvideos.csv in data/ or specify --input <path_to_csv>.")
        sys.exit(1)

    category_map, _ = load_category_mappings()

    # 3. Initialize SparkSession
    print("\n[3/5] Starting Apache SparkSession (local[*] multi-core)...")
    spark = get_spark_session("YouTubeTrendingBatchJob")
    print(f"✓ SparkSession active: Version {spark.version}, Master: {spark.sparkContext.master}")

    # 4. Distributed Processing Pipeline
    print("\n[4/5] Executing PySpark DataFrame DAG (Ingest, Clean, Deduplicate, Enrich)...")
    spark_df, metrics = process_with_pyspark(spark, str(input_file), category_map)

    print(f"\n--- PySpark Execution Metrics ---")
    print(f"  • Raw Records Ingested   : {metrics['raw_record_count']:,}")
    print(f"  • Clean Records Retained : {metrics['clean_record_count']:,}")
    print(f"  • Deduplicated / Dropped : {metrics['records_dropped']:,}")
    print(f"  • Spark RDD Partitions   : {metrics['spark_partitions']}")
    print(f"  • Spark Processing Time  : {metrics['spark_execution_time_seconds']} seconds")

    # 5. Execute Spark SQL Analytics
    print("\n[5/5] Executing Spark SQL Analytics Queries...")

    print("\n--- [Query A] Top 5 Most-Viewed Trending Videos ---")
    top_v_sql = """
    SELECT video_id, title, channel_title, views, likes, comment_count, like_view_ratio
    FROM trending_videos
    ORDER BY views DESC
    LIMIT 5
    """
    top_videos = run_spark_sql(spark, top_v_sql)
    print(top_videos[["title", "channel_title", "views", "likes", "like_view_ratio"]].to_string(index=False))

    print("\n--- [Query B] Top 5 Categories by Total Views ---")
    cat_summary = get_spark_category_summary(spark_df)
    print(cat_summary[["category_name", "trending_records", "total_views", "avg_views"]].head(5).to_string(index=False))

    print("\n--- [Query C] Top 5 Channels by Trending Frequency ---")
    chan_summary = get_spark_channel_summary(spark_df, limit=5)
    print(chan_summary[["channel_title", "trending_records", "total_views", "avg_views_per_record"]].to_string(index=False))

    spark.stop()
    print("\n" + "=" * 70)
    print("✓ PySpark Job Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
