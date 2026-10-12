"""
Visualizations Module for YouTube Trending Video Analytics.
Provides responsive, YouTube-themed interactive Plotly charts.
"""

from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import THEME_COLORS


def apply_youtube_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """
    Applies YouTube-inspired dark aesthetics to a Plotly figure.
    """
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "y": 0.95,
            "x": 0.05,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 16, "color": THEME_COLORS["text_primary"]},
        },
        paper_bgcolor=THEME_COLORS["card_bg"],
        plot_bgcolor=THEME_COLORS["card_bg"],
        font={"color": THEME_COLORS["text_primary"], "family": "Arial, sans-serif"},
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(
            gridcolor=THEME_COLORS["border_color"],
            zerolinecolor=THEME_COLORS["border_color"],
            showline=True,
            linecolor=THEME_COLORS["border_color"],
        ),
        yaxis=dict(
            gridcolor=THEME_COLORS["border_color"],
            zerolinecolor=THEME_COLORS["border_color"],
            showline=True,
            linecolor=THEME_COLORS["border_color"],
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=THEME_COLORS["border_color"],
            font=dict(color=THEME_COLORS["text_primary"]),
        ),
    )
    return fig


def plot_top_videos(df: pd.DataFrame, metric: str = "views", top_n: int = 10) -> go.Figure:
    """
    Generates a horizontal bar chart of the top videos by the selected metric.
    """
    if df.empty or metric not in df.columns:
        fig = go.Figure()
        return apply_youtube_theme(fig, "No Video Data Available")

    # Limit title length for readable chart labels
    plot_df = df.copy().head(top_n)
    plot_df["display_title"] = plot_df["title"].apply(
        lambda t: (t[:45] + "...") if len(t) > 48 else t
    )
    # Sort ascending for horizontal bar chart (top video at the top)
    plot_df = plot_df.sort_values(by=metric, ascending=True)

    metric_label = metric.replace("_", " ").title()
    bar_color = THEME_COLORS["primary_red"] if metric == "views" else THEME_COLORS["accent_blue"]

    fig = go.Figure(
        go.Bar(
            x=plot_df[metric],
            y=plot_df["display_title"],
            orientation="h",
            marker=dict(
                color=bar_color,
                line=dict(color="#FFFFFF", width=0.5),
            ),
            customdata=plot_df[["channel_title", "views", "likes", "comment_count"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Channel: %{customdata[0]}<br>"
                f"{metric_label}: %{{x:,.0f}}<br>"
                "Total Views: %{customdata[1]:,.0f}<br>"
                "Total Likes: %{customdata[2]:,.0f}<br>"
                "Total Comments: %{customdata[3]:,.0f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title=metric_label,
        yaxis_title="Video Title",
        height=450,
    )
    return apply_youtube_theme(fig, f"Top {top_n} Videos by {metric_label}")


def plot_category_bar(
    df: pd.DataFrame, metric: str = "total_views", title_suffix: str = "Total Views"
) -> go.Figure:
    """
    Generates a vertical bar chart of categories ranked by metric.
    """
    if df.empty or metric not in df.columns:
        fig = go.Figure()
        return apply_youtube_theme(fig, "No Category Data Available")

    sorted_df = df.sort_values(by=metric, ascending=False).head(15)

    colors = [
        THEME_COLORS["primary_red"],
        THEME_COLORS["accent_blue"],
        THEME_COLORS["accent_green"],
        THEME_COLORS["accent_yellow"],
        THEME_COLORS["accent_purple"],
    ]

    fig = px.bar(
        sorted_df,
        x="category_name",
        y=metric,
        color="category_name",
        color_discrete_sequence=colors * 3,
        hover_data={"category_name": True, metric: ":,.0f"},
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title=metric.replace("_", " ").title(),
        showlegend=False,
        height=450,
    )
    fig.update_xaxes(tickangle=-40)
    return apply_youtube_theme(fig, f"Category Comparison: {title_suffix}")


def plot_channel_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Generates a bar chart of channels with the most trending videos.
    """
    if df.empty or "trending_records" not in df.columns:
        fig = go.Figure()
        return apply_youtube_theme(fig, "No Channel Data Available")

    plot_df = df.head(top_n).sort_values(by="trending_records", ascending=True)

    fig = go.Figure(
        go.Bar(
            x=plot_df["trending_records"],
            y=plot_df["channel_title"],
            orientation="h",
            marker=dict(color=THEME_COLORS["accent_blue"]),
            customdata=plot_df[["total_views", "unique_videos"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Trending Records: %{x}<br>"
                "Unique Videos: %{customdata[1]}<br>"
                "Total Views: %{customdata[0]:,.0f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Trending Video Records",
        yaxis_title="Channel Name",
        height=480,
    )
    return apply_youtube_theme(fig, f"Top {top_n} Channels by Trending Volume")


def plot_engagement_scatter(
    df: pd.DataFrame,
    x_col: str = "views",
    y_col: str = "likes",
    sample_size: int = 1500,
) -> go.Figure:
    """
    Generates an interactive scatter plot showing the relationship between views and engagement.
    Uses downsampling for responsiveness on large datasets.
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        fig = go.Figure()
        return apply_youtube_theme(fig, "No Engagement Data Available")

    plot_df = df.sample(min(len(df), sample_size), random_state=42) if len(df) > sample_size else df

    fig = px.scatter(
        plot_df,
        x=x_col,
        y=y_col,
        color="category_name" if "category_name" in plot_df.columns else None,
        hover_name="title" if "title" in plot_df.columns else None,
        hover_data={
            "channel_title": True if "channel_title" in plot_df.columns else False,
            x_col: ":,.0f",
            y_col: ":,.0f",
        },
        opacity=0.75,
    )

    fig.update_layout(
        xaxis_title=x_col.replace("_", " ").title(),
        yaxis_title=y_col.replace("_", " ").title(),
        height=500,
    )
    return apply_youtube_theme(
        fig, f"Engagement Relationship: {y_col.title()} vs. {x_col.title()}"
    )


def plot_timeline_trends(daily_df: pd.DataFrame) -> go.Figure:
    """
    Plots a time-series area/line chart of trending records and viewership over time.
    """
    if daily_df.empty or "date" not in daily_df.columns:
        fig = go.Figure()
        return apply_youtube_theme(fig, "No Timeline Data Available")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily_df["date"],
            y=daily_df["trending_records"],
            mode="lines+markers",
            name="Trending Records",
            line=dict(color=THEME_COLORS["primary_red"], width=2),
            marker=dict(size=4),
            fill="tozeroy",
            fillcolor="rgba(255, 0, 0, 0.15)",
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Trending Records Count",
        height=400,
    )
    return apply_youtube_theme(fig, "Daily Trending Records Timeline")


def plot_day_of_week(dow_df: pd.DataFrame) -> go.Figure:
    """
    Plots a bar chart showing trending frequency by day of the week.
    """
    if dow_df.empty or "day_name" not in dow_df.columns:
        fig = go.Figure()
        return apply_youtube_theme(fig, "No Day of Week Data Available")

    fig = go.Figure(
        go.Bar(
            x=dow_df["day_name"],
            y=dow_df["record_count"],
            marker=dict(color=THEME_COLORS["accent_yellow"]),
            text=dow_df["record_count"],
            textposition="outside",
        )
    )

    fig.update_layout(
        xaxis_title="Day of Week",
        yaxis_title="Record Count",
        height=350,
    )
    return apply_youtube_theme(fig, "Trending Frequency by Day of Week")


def plot_data_retention_pie(summary: dict) -> go.Figure:
    """
    Generates a donut chart displaying data cleaning retention vs dropped rows.
    """
    final_rows = summary.get("final_rows", 0)
    removed_rows = summary.get("total_rows_removed", 0)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Clean Retained Records", "Removed / Dropped"],
                values=[final_rows, removed_rows],
                hole=0.55,
                marker=dict(
                    colors=[THEME_COLORS["accent_green"], THEME_COLORS["primary_red"]]
                ),
            )
        ]
    )

    fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    return apply_youtube_theme(fig, "Data Cleaning Retention")
