"""
Unit tests for analytics module.
Tests KPI calculations, top video rankings, category aggregations,
channel metrics, engagement distributions, and time-based patterns.
"""

import pandas as pd
import pytest

from src.analytics import (
    get_category_analytics,
    get_channel_analytics,
    get_engagement_metrics,
    get_overview_kpis,
    get_time_based_analytics,
    get_top_videos,
)
from src.data_cleaner import clean_trending_data


@pytest.fixture
def clean_test_dataset():
    raw_df = pd.DataFrame({
        "video_id": ["v1", "v2", "v3", "v4"],
        "trending_date": ["17.14.11", "17.14.11", "17.15.11", "17.15.11"],
        "title": ["Song Track", "Comedy Sketch", "News Update", "Tech Review"],
        "channel_title": ["Music Label", "Comedy Central", "News Network", "Tech Central"],
        "category_id": [10, 23, 25, 28],
        "views": [500000, 200000, 100000, 50000],
        "likes": [25000, 12000, 3000, 4000],
        "comment_count": [2000, 1500, 800, 600],
    })
    category_map = {10: "Music", 23: "Comedy", 25: "News & Politics", 28: "Science & Technology"}
    cleaned, _ = clean_trending_data(raw_df, category_map)
    return cleaned


def test_get_overview_kpis(clean_test_dataset):
    kpis = get_overview_kpis(clean_test_dataset)
    assert kpis["total_records"] == 4
    assert kpis["unique_videos"] == 4
    assert kpis["unique_channels"] == 4
    assert kpis["total_views"] == 850000
    assert kpis["total_likes"] == 44000
    assert kpis["total_comments"] == 4900
    assert kpis["avg_views"] == 212500.0
    assert kpis["overall_like_ratio"] > 0


def test_get_top_videos_by_views(clean_test_dataset):
    top_videos = get_top_videos(clean_test_dataset, metric="views", top_n=2)
    assert len(top_videos) == 2
    assert top_videos.iloc[0]["video_id"] == "v1"
    assert top_videos.iloc[0]["views"] == 500000
    assert top_videos.iloc[1]["video_id"] == "v2"


def test_get_top_videos_by_likes(clean_test_dataset):
    top_videos = get_top_videos(clean_test_dataset, metric="likes", top_n=1)
    assert len(top_videos) == 1
    assert top_videos.iloc[0]["video_id"] == "v1"
    assert top_videos.iloc[0]["likes"] == 25000


def test_get_category_analytics(clean_test_dataset):
    cat_df = get_category_analytics(clean_test_dataset)
    assert len(cat_df) == 4
    assert "category_name" in cat_df.columns
    assert "total_views" in cat_df.columns
    assert "avg_views" in cat_df.columns
    # Music has the highest views
    assert cat_df.iloc[0]["category_name"] == "Music"
    assert cat_df.iloc[0]["total_views"] == 500000


def test_get_channel_analytics(clean_test_dataset):
    chan_df = get_channel_analytics(clean_test_dataset, min_records=1, top_n=5)
    assert len(chan_df) == 4
    assert "channel_title" in chan_df.columns
    assert "trending_records" in chan_df.columns


def test_get_engagement_metrics(clean_test_dataset):
    eng = get_engagement_metrics(clean_test_dataset)
    assert "views_likes_corr" in eng
    assert "percentiles" in eng
    assert "views_p50" in eng["percentiles"]


def test_get_time_based_analytics(clean_test_dataset):
    time_res = get_time_based_analytics(clean_test_dataset)
    assert time_res["has_trending_date"] is True
    assert not time_res["daily_trends"].empty
    assert not time_res["day_of_week"].empty
