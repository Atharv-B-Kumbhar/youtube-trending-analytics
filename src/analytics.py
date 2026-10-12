"""
Analytics Engine Module for YouTube Trending Video Analytics.
Computes summary metrics, top videos, category aggregations, channel performance,
engagement correlations, and time-series patterns.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def get_overview_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes high-level overview KPIs for the dashboard header.
    """
    total_records = len(df)
    if total_records == 0:
        return {
            "total_records": 0,
            "unique_videos": 0,
            "unique_channels": 0,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "avg_views": 0,
            "avg_likes": 0,
            "avg_comments": 0,
            "overall_like_ratio": 0.0,
            "overall_comment_ratio": 0.0,
        }

    total_views = int(df["views"].sum())
    total_likes = int(df["likes"].sum()) if "likes" in df.columns else 0
    total_comments = int(df["comment_count"].sum()) if "comment_count" in df.columns else 0

    return {
        "total_records": total_records,
        "unique_videos": int(df["video_id"].nunique()),
        "unique_channels": int(df["channel_title"].nunique()),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "avg_views": float(df["views"].mean()),
        "avg_likes": float(df["likes"].mean()) if "likes" in df.columns else 0.0,
        "avg_comments": float(df["comment_count"].mean()) if "comment_count" in df.columns else 0.0,
        "overall_like_ratio": round((total_likes / total_views * 100), 2) if total_views > 0 else 0.0,
        "overall_comment_ratio": round((total_comments / total_views * 100), 2) if total_views > 0 else 0.0,
    }


def get_top_videos(
    df: pd.DataFrame,
    metric: str = "views",
    top_n: int = 10,
    dedup_by_video_id: bool = True,
) -> pd.DataFrame:
    """
    Retrieves the top N videos sorted by the selected metric (views, likes, comment_count, like_view_ratio).
    If dedup_by_video_id is True, picks the latest/max record per video_id so the same video
    doesn't appear multiple times across different trending days.
    """
    if df.empty or metric not in df.columns:
        return pd.DataFrame()

    cols_to_keep = [
        "video_id",
        "title",
        "channel_title",
        "category_name",
        "views",
        "likes",
        "comment_count",
    ]
    if "dislikes" in df.columns:
        cols_to_keep.append("dislikes")
    if "like_view_ratio" in df.columns:
        cols_to_keep.append("like_view_ratio")
    if "trending_date" in df.columns:
        cols_to_keep.append("trending_date")

    subset = df[[col for col in cols_to_keep if col in df.columns]].copy()

    if dedup_by_video_id:
        subset = subset.sort_values(by=metric, ascending=False).drop_duplicates(
            subset=["video_id"], keep="first"
        )
    else:
        subset = subset.sort_values(by=metric, ascending=False)

    return subset.head(top_n).reset_index(drop=True)


def get_category_analytics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates performance statistics grouped by category.
    """
    if df.empty or "category_name" not in df.columns:
        return pd.DataFrame()

    agg_dict = {
        "video_id": ["count", "nunique"],
        "views": ["sum", "mean", "median"],
    }
    if "likes" in df.columns:
        agg_dict["likes"] = ["sum", "mean"]
    if "comment_count" in df.columns:
        agg_dict["comment_count"] = ["sum", "mean"]
    if "like_view_ratio" in df.columns:
        agg_dict["like_view_ratio"] = ["mean"]

    grouped = df.groupby("category_name").agg(agg_dict)

    # Flatten multi-level columns
    grouped.columns = [f"{col}_{stat}" for col, stat in grouped.columns]
    grouped = grouped.reset_index()

    # Rename to clean labels
    rename_map = {
        "video_id_count": "trending_records",
        "video_id_nunique": "unique_videos",
        "views_sum": "total_views",
        "views_mean": "avg_views",
        "views_median": "median_views",
        "likes_sum": "total_likes",
        "likes_mean": "avg_likes",
        "comment_count_sum": "total_comments",
        "comment_count_mean": "avg_comments",
        "like_view_ratio_mean": "avg_like_ratio",
    }
    grouped = grouped.rename(columns=rename_map)
    grouped = grouped.sort_values(by="total_views", ascending=False).reset_index(drop=True)

    # Format numeric columns for presentation
    grouped["avg_views"] = grouped["avg_views"].round(1)
    if "avg_likes" in grouped.columns:
        grouped["avg_likes"] = grouped["avg_likes"].round(1)
    if "avg_comments" in grouped.columns:
        grouped["avg_comments"] = grouped["avg_comments"].round(1)
    if "avg_like_ratio" in grouped.columns:
        grouped["avg_like_ratio"] = grouped["avg_like_ratio"].round(2)

    return grouped


def get_channel_analytics(
    df: pd.DataFrame,
    min_records: int = 1,
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Aggregates metrics by channel to find the top channels by trending frequency and viewership.
    """
    if df.empty or "channel_title" not in df.columns:
        return pd.DataFrame()

    agg_dict = {
        "video_id": ["count", "nunique"],
        "views": ["sum", "mean"],
    }
    if "likes" in df.columns:
        agg_dict["likes"] = ["sum", "mean"]
    if "comment_count" in df.columns:
        agg_dict["comment_count"] = ["sum"]

    grouped = df.groupby("channel_title").agg(agg_dict)
    grouped.columns = [f"{col}_{stat}" for col, stat in grouped.columns]
    grouped = grouped.reset_index()

    rename_map = {
        "video_id_count": "trending_records",
        "video_id_nunique": "unique_videos",
        "views_sum": "total_views",
        "views_mean": "avg_views_per_record",
        "likes_sum": "total_likes",
        "likes_mean": "avg_likes",
        "comment_count_sum": "total_comments",
    }
    grouped = grouped.rename(columns=rename_map)

    # Filter by minimum trending records to filter out single-hit anomalies
    if min_records > 1:
        grouped = grouped[grouped["trending_records"] >= min_records]

    grouped["avg_views_per_record"] = grouped["avg_views_per_record"].round(1)
    if "avg_likes" in grouped.columns:
        grouped["avg_likes"] = grouped["avg_likes"].round(1)

    return grouped.sort_values(by="trending_records", ascending=False).head(top_n).reset_index(drop=True)


def get_engagement_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes engagement distributions and Pearson correlation coefficients
    between views, likes, and comments.
    """
    if df.empty:
        return {
            "views_likes_corr": 0.0,
            "views_comments_corr": 0.0,
            "likes_comments_corr": 0.0,
            "avg_like_ratio": 0.0,
            "avg_comment_ratio": 0.0,
            "percentiles": {},
        }

    # Correlations
    cols_for_corr = [c for c in ["views", "likes", "comment_count"] if c in df.columns]
    corr_matrix = df[cols_for_corr].corr() if len(cols_for_corr) > 1 else pd.DataFrame()

    v_l_corr = float(corr_matrix.loc["views", "likes"]) if "views" in corr_matrix and "likes" in corr_matrix else 0.0
    v_c_corr = float(corr_matrix.loc["views", "comment_count"]) if "views" in corr_matrix and "comment_count" in corr_matrix else 0.0
    l_c_corr = float(corr_matrix.loc["likes", "comment_count"]) if "likes" in corr_matrix and "comment_count" in corr_matrix else 0.0

    percentiles = {
        "views_p50": float(df["views"].median()),
        "views_p75": float(df["views"].quantile(0.75)),
        "views_p95": float(df["views"].quantile(0.95)),
    }
    if "likes" in df.columns:
        percentiles["likes_p50"] = float(df["likes"].median())
        percentiles["likes_p75"] = float(df["likes"].quantile(0.75))
    if "comment_count" in df.columns:
        percentiles["comments_p50"] = float(df["comment_count"].median())
        percentiles["comments_p75"] = float(df["comment_count"].quantile(0.75))

    return {
        "views_likes_corr": round(v_l_corr, 3),
        "views_comments_corr": round(v_c_corr, 3),
        "likes_comments_corr": round(l_c_corr, 3),
        "avg_like_ratio": round(float(df["like_view_ratio"].mean()), 2) if "like_view_ratio" in df.columns else 0.0,
        "avg_comment_ratio": round(float(df["comment_view_ratio"].mean()), 2) if "comment_view_ratio" in df.columns else 0.0,
        "percentiles": percentiles,
    }


def get_time_based_analytics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregates trending patterns over time, days of the week, and publishing hours.
    """
    results: Dict[str, Any] = {
        "has_trending_date": False,
        "has_publish_time": False,
        "daily_trends": pd.DataFrame(),
        "day_of_week": pd.DataFrame(),
        "publish_hour": pd.DataFrame(),
    }

    if df.empty:
        return results

    # Daily trending timeline
    if "trending_date_parsed" in df.columns and df["trending_date_parsed"].notna().any():
        valid_tdate = df[df["trending_date_parsed"].notna()].copy()
        if not valid_tdate.empty:
            results["has_trending_date"] = True
            daily = valid_tdate.groupby(valid_tdate["trending_date_parsed"].dt.date).agg(
                trending_records=("video_id", "count"),
                total_views=("views", "sum"),
                avg_views=("views", "mean"),
            ).reset_index()
            daily.rename(columns={"trending_date_parsed": "date"}, inplace=True)
            results["daily_trends"] = daily.sort_values(by="date")

            # Day of week
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dow = valid_tdate["trending_day_name"].value_counts().reindex(days_order).fillna(0).reset_index()
            dow.columns = ["day_name", "record_count"]
            results["day_of_week"] = dow

    # Publish Hour Distribution
    if "publish_hour" in df.columns and (df["publish_hour"] >= 0).any():
        valid_pub = df[df["publish_hour"] >= 0]
        if not valid_pub.empty:
            results["has_publish_time"] = True
            pub_hours = valid_pub["publish_hour"].value_counts().sort_index().reset_index()
            pub_hours.columns = ["hour", "video_count"]
            results["publish_hour"] = pub_hours

    return results
