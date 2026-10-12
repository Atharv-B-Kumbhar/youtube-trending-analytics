"""
Data Cleaner Module for YouTube Trending Video Analytics.
Provides robust data cleaning, deduplication, schema normalization,
safe numeric conversion, date parsing, and cleaning summary metrics.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd

from config import (
    OPTIONAL_DATE_COLUMNS,
    OPTIONAL_NUMERIC_COLUMNS,
    REQUIRED_COLUMNS,
)
from src.data_loader import validate_schema


def clean_trending_data(
    df: pd.DataFrame,
    category_map: Optional[Dict[int, str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw YouTube trending data according to robust data engineering practices:
    1. Validates required columns.
    2. Removes exact daily duplicate records using [video_id, trending_date].
    3. Safely coerces numeric metrics (views, likes, dislikes, comment_count).
    4. Handles non-positive or corrupted views, negative counts.
    5. Safely parses dates (trending_date and publish_time) without crashing on invalid formats.
    6. Maps category IDs to human-readable category names.
    7. Computes engagement ratios safely (like_view_ratio, comment_view_ratio).
    8. Preserves Unicode text (titles, channel names, descriptions).
    9. Produces a comprehensive data cleaning summary report.

    Returns:
        tuple: (cleaned_df: pd.DataFrame, cleaning_summary: dict)
    """
    # 1. Validate Schema
    is_valid, missing_cols, present_cols, error_msg = validate_schema(df)
    if not is_valid:
        raise ValueError(error_msg)

    # Work on a copy
    df = df.copy()
    initial_rows = len(df)
    summary: Dict[str, Any] = {
        "initial_rows": initial_rows,
        "missing_values_by_column": {},
        "duplicates_removed": 0,
        "rows_with_invalid_views_dropped": 0,
        "invalid_trending_dates": 0,
        "invalid_publish_times": 0,
        "columns_present": list(df.columns),
        "has_dislikes": "dislikes" in df.columns,
        "has_trending_date": "trending_date" in df.columns,
        "has_publish_time": "publish_time" in df.columns,
    }

    # Record initial missing value counts
    for col in df.columns:
        summary["missing_values_by_column"][col] = int(df[col].isna().sum())

    # 2. Text Normalization and Unicode Preservation
    for col in ["title", "channel_title"]:
        if col in df.columns:
            df[col] = df[col].fillna(f"Unknown {col.replace('_', ' ').title()}")
            df[col] = df[col].astype(str).str.strip()

    if "description" in df.columns:
        df["description"] = df["description"].fillna("").astype(str)

    # 3. Category ID Normalization & Mapping
    df["category_id"] = pd.to_numeric(df["category_id"], errors="coerce").fillna(0).astype(int)
    if category_map:
        df["category_name"] = df["category_id"].apply(
            lambda cid: category_map.get(cid, f"Category {cid}")
        )
    else:
        df["category_name"] = df["category_id"].apply(lambda cid: f"Category {cid}")

    # 4. Safe Numeric Conversion
    # views is mandatory
    df["views"] = pd.to_numeric(df["views"], errors="coerce")
    # Drop rows where views is NaN or negative (cannot compute valid analytics)
    valid_views_mask = df["views"].notna() & (df["views"] >= 0)
    invalid_views_count = int((~valid_views_mask).sum())
    summary["rows_with_invalid_views_dropped"] = invalid_views_count
    df = df[valid_views_mask].copy()
    df["views"] = df["views"].astype(np.int64)

    # Optional numeric columns (likes, dislikes, comment_count)
    for num_col in OPTIONAL_NUMERIC_COLUMNS:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)
            # Clip negative counts to 0 (corrupted logs)
            df[num_col] = df[num_col].apply(lambda x: max(0, x)).astype(np.int64)
        else:
            df[num_col] = 0

    # 5. Date Parsing
    # Trending date: format is usually YY.DD.MM in Kaggle datasets, e.g. '17.14.11'
    if "trending_date" in df.columns:
        raw_trending = df["trending_date"].astype(str).str.strip()
        # Try Kaggle format YY.DD.MM first
        parsed_dates = pd.to_datetime(raw_trending, format="%y.%d.%m", errors="coerce")
        # For dates that failed, attempt standard parser
        fallback_mask = parsed_dates.isna()
        if fallback_mask.any():
            parsed_fallback = pd.to_datetime(raw_trending[fallback_mask], errors="coerce")
            parsed_dates.update(parsed_fallback)

        invalid_tdate_count = int(parsed_dates.isna().sum())
        summary["invalid_trending_dates"] = invalid_tdate_count
        df["trending_date_parsed"] = parsed_dates
        df["trending_day_name"] = df["trending_date_parsed"].dt.day_name()
        df["trending_month"] = df["trending_date_parsed"].dt.strftime("%Y-%m")
    else:
        df["trending_date_parsed"] = pd.NaT
        df["trending_day_name"] = "Unknown"
        df["trending_month"] = "Unknown"

    # Publish time: ISO 8601 like '2017-11-13T17:00:00.000Z'
    if "publish_time" in df.columns:
        parsed_pub = pd.to_datetime(df["publish_time"], errors="coerce", utc=True)
        summary["invalid_publish_times"] = int(parsed_pub.isna().sum())
        df["publish_time_parsed"] = parsed_pub
        df["publish_hour"] = df["publish_time_parsed"].dt.hour
    else:
        df["publish_time_parsed"] = pd.NaT
        df["publish_hour"] = -1

    # 6. Deduplication
    # Daily trending deduplication: same video_id on the same trending_date
    pre_dedup_count = len(df)
    if "trending_date" in df.columns:
        df = df.drop_duplicates(subset=["video_id", "trending_date"], keep="last")
    else:
        df = df.drop_duplicates(subset=["video_id"], keep="last")
    summary["duplicates_removed"] = int(pre_dedup_count - len(df))

    # 7. Engagement Ratios (with Safe Zero-Views Division)
    # Ratios expressed as percentages (%)
    views_series = df["views"].replace(0, np.nan)
    df["like_view_ratio"] = ((df["likes"] / views_series) * 100).fillna(0.0).round(4)
    df["comment_view_ratio"] = ((df["comment_count"] / views_series) * 100).fillna(0.0).round(4)
    if summary["has_dislikes"]:
        df["dislike_view_ratio"] = ((df["dislikes"] / views_series) * 100).fillna(0.0).round(4)
    else:
        df["dislike_view_ratio"] = 0.0

    # 8. Final Summary Construction
    final_rows = len(df)
    summary["final_rows"] = final_rows
    summary["total_rows_removed"] = initial_rows - final_rows
    summary["retention_rate_pct"] = (
        round((final_rows / initial_rows) * 100, 2) if initial_rows > 0 else 0.0
    )

    return df, summary
