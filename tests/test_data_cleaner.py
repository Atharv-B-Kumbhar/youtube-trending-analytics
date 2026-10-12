"""
Unit tests for data_cleaner module.
Tests deduplication, missing values, invalid numbers, zero-view safety,
date parsing, and Unicode preservation.
"""

import pandas as pd
import pytest

from src.data_cleaner import clean_trending_data


@pytest.fixture
def sample_raw_dataframe():
    """
    Creates a synthetic fixture simulating Kaggle YouTube trending dataset
    with various dirty-data edge cases:
    - Unicode characters in title
    - Exact duplicate daily record
    - Corrupted numeric strings
    - Negative counts
    - Zero views video
    - Missing title and missing optional columns
    """
    return pd.DataFrame({
        "video_id": ["v1", "v1", "v2", "v3", "v4", "v5"],
        "trending_date": ["17.14.11", "17.14.11", "17.15.11", "17.15.11", "invalid_date", "17.16.11"],
        "title": [
            "T-Series Official Video - गुरु रंधावा",
            "T-Series Official Video - गुरु रंधावा",  # Duplicate row
            "Big Data Analytics Lecture",
            None,  # Missing title
            "Zero Views Video",
            "Corrupted Views Video",
        ],
        "channel_title": ["T-Series", "T-Series", "IIT Tech", "Unknown", "Channel A", "Channel B"],
        "category_id": [10, 10, 27, 24, 20, 24],
        "publish_time": [
            "2017-11-13T17:00:00.000Z",
            "2017-11-13T17:00:00.000Z",
            "2017-11-14T08:30:00.000Z",
            "2017-11-14T10:00:00.000Z",
            "2017-11-15T12:00:00.000Z",
            "2017-11-15T14:00:00.000Z",
        ],
        "views": [1000000, 1000000, 50000, 20000, 0, "NOT_A_NUMBER"],  # string and zero
        "likes": [50000, 50000, 2500, -100, 0, 50],  # negative likes
        "dislikes": [1000, 1000, 50, 10, 0, 5],
        "comment_count": [8000, 8000, 400, 150, 0, 10],
    })


def test_clean_trending_data_deduplication(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    # v1 had 2 identical rows for '17.14.11'; one should be removed
    assert summary["duplicates_removed"] == 1
    assert len(cleaned_df[cleaned_df["video_id"] == "v1"]) == 1


def test_clean_trending_data_invalid_views_dropped(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    # v5 had 'NOT_A_NUMBER' for views -> dropped
    assert summary["rows_with_invalid_views_dropped"] == 1
    assert "v5" not in cleaned_df["video_id"].values


def test_clean_trending_data_zero_views_safety(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    # v4 has 0 views
    zero_view_row = cleaned_df[cleaned_df["video_id"] == "v4"]
    assert len(zero_view_row) == 1
    # Engagement ratios should be safely 0.0 and NOT NaN or Infinity
    assert zero_view_row.iloc[0]["like_view_ratio"] == 0.0
    assert zero_view_row.iloc[0]["comment_view_ratio"] == 0.0


def test_clean_trending_data_negative_likes_clipped(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    # v3 had -100 likes -> clipped to 0
    v3_row = cleaned_df[cleaned_df["video_id"] == "v3"]
    assert v3_row.iloc[0]["likes"] == 0


def test_clean_trending_data_unicode_preserved(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    v1_row = cleaned_df[cleaned_df["video_id"] == "v1"]
    assert "गुरु रंधावा" in v1_row.iloc[0]["title"]


def test_clean_trending_data_missing_title_handled(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    v3_row = cleaned_df[cleaned_df["video_id"] == "v3"]
    assert "Unknown Title" in v3_row.iloc[0]["title"]


def test_clean_trending_data_date_parsing(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    v1_row = cleaned_df[cleaned_df["video_id"] == "v1"]
    # 17.14.11 -> 2017-11-14
    parsed_date = v1_row.iloc[0]["trending_date_parsed"]
    assert parsed_date.year == 2017
    assert parsed_date.month == 11
    assert parsed_date.day == 14
    # invalid_date was detected
    assert summary["invalid_trending_dates"] >= 1


def test_clean_trending_data_ratio_calculation(sample_raw_dataframe):
    cleaned_df, summary = clean_trending_data(sample_raw_dataframe)
    # v1: 50000 likes / 1000000 views = 5.0%
    v1_row = cleaned_df[cleaned_df["video_id"] == "v1"]
    assert abs(v1_row.iloc[0]["like_view_ratio"] - 5.0) < 0.001
    # comments: 8000 / 1000000 = 0.8%
    assert abs(v1_row.iloc[0]["comment_view_ratio"] - 0.8) < 0.001


def test_clean_trending_data_missing_required_column_raises():
    bad_df = pd.DataFrame({"title": ["Test"]})
    with pytest.raises(ValueError) as excinfo:
        clean_trending_data(bad_df)
    assert "Missing required column" in str(excinfo.value)
