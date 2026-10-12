"""
Unit tests for PySpark processing module.
Tests SparkSession creation, DataFrame transformation, distributed deduplication,
and Spark SQL query execution with OpenJDK.
"""

import tempfile
from pathlib import Path
import pandas as pd
import pytest

from src.pyspark_processor import (
    check_spark_environment,
    get_spark_category_summary,
    get_spark_channel_summary,
    get_spark_session,
    process_with_pyspark,
    run_spark_sql,
)


def test_spark_environment_ready():
    env = check_spark_environment()
    assert env["pyspark_installed"] is True
    assert env["java_installed"] is True
    assert env["is_ready"] is True


def test_pyspark_end_to_end_pipeline():
    env = check_spark_environment()
    if not env["is_ready"]:
        pytest.skip("Java runtime not available")

    # Create temporary CSV fixture
    csv_content = """video_id,trending_date,title,channel_title,category_id,publish_time,tags,views,likes,dislikes,comment_count
vid1,17.14.11,Spark Big Data 101,Apache Foundation,28,2017-11-13T17:00:00.000Z,spark|bda,150000,12000,150,850
vid1,17.14.11,Spark Big Data 101,Apache Foundation,28,2017-11-13T17:00:00.000Z,spark|bda,150000,12000,150,850
vid2,17.15.11,Python Analytics,Data Science Hub,27,2017-11-14T10:00:00.000Z,python,95000,7500,80,420
vid3,17.15.11,Zero Views Edge Case,Test Channel,20,2017-11-14T12:00:00.000Z,test,0,0,0,0
"""
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        spark = get_spark_session("PySparkUnitTest")
        spark_df, metrics = process_with_pyspark(spark, temp_path)

        # vid1 was duplicated on same trending_date -> should be deduplicated to 3 records
        assert metrics["raw_record_count"] == 4
        assert metrics["clean_record_count"] == 3
        assert metrics["records_dropped"] == 1

        # Test Spark SQL Query
        sql_res = run_spark_sql(spark, "SELECT title, views, like_view_ratio FROM trending_videos ORDER BY views DESC")
        assert len(sql_res) == 3
        assert sql_res.iloc[0]["title"] == "Spark Big Data 101"

        # Safe ratio check on zero views
        zero_row = sql_res[sql_res["title"] == "Zero Views Edge Case"]
        assert len(zero_row) == 1
        assert zero_row.iloc[0]["like_view_ratio"] == 0.0

        # Category summary
        cat_df = get_spark_category_summary(spark_df)
        assert len(cat_df) >= 2

        # Channel summary
        chan_df = get_spark_channel_summary(spark_df, limit=5)
        assert len(chan_df) >= 2

        spark.stop()
    finally:
        Path(temp_path).unlink(missing_ok=True)
