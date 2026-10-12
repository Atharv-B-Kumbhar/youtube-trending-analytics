"""
YouTube Trending Video Analytics Using Big Data Technologies
Streamlit Interactive Web Application
"""

import io
from pathlib import Path
import pandas as pd
import streamlit as st

from config import DATA_DIR, DEFAULT_CATEGORY_JSON, DEFAULT_CSV_PATH, THEME_COLORS
from src.analytics import (
    get_category_analytics,
    get_channel_analytics,
    get_engagement_metrics,
    get_overview_kpis,
    get_time_based_analytics,
    get_top_videos,
)
from src.data_cleaner import clean_trending_data
from src.data_loader import load_category_mappings, load_csv_data
from src.pyspark_processor import (
    check_spark_environment,
    get_spark_session,
    process_with_pyspark,
    run_spark_sql,
)
from src.visualizations import (
    plot_category_bar,
    plot_channel_bar,
    plot_data_retention_pie,
    plot_day_of_week,
    plot_engagement_scatter,
    plot_timeline_trends,
    plot_top_videos,
)

# Page Configuration
st.set_page_config(
    page_title="YouTube Trending Analytics | Big Data",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (YouTube Dark Aesthetic)
st.markdown(
    """
    <style>
    .main {
        background-color: #0F0F0F;
        color: #FFFFFF;
    }
    .metric-card {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .metric-title {
        color: #AAAAAA;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .metric-sub {
        color: #3EA6FF;
        font-size: 0.8rem;
        margin-top: 4px;
    }
    .badge-yt {
        background-color: #FF0000;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .info-box {
        background-color: #1a2234;
        border-left: 4px solid #3EA6FF;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 16px;
        font-size: 0.9rem;
    }
    .caution-box {
        background-color: #2b1f1f;
        border-left: 4px solid #FFD600;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 16px;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_and_clean_data(file_source, category_map):
    """
    Loads and cleans data with Streamlit caching.
    """
    raw_df, meta = load_csv_data(file_source)
    cleaned_df, summary = clean_trending_data(raw_df, category_map)
    return raw_df, cleaned_df, meta, summary


def main():
    # Sidebar Header
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 22px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 68 48" width="38" height="26">
                <path fill="#FF0000" d="M66.52,7.74c-0.78-2.93-3.09-5.24-6.02-6.02C55.21,0.4,34,0.4,34,0.4s-21.21,0-26.5,1.32 c-2.94,0.78-5.24,3.09-6.02,6.02C0.16,13.03,0.16,24,0.16,24s0,10.97,1.32,16.26c0.78,2.93,3.08,5.24,6.02,6.02 C12.79,47.6,34,47.6,34,47.6s21.21,0,26.5-1.32c2.93-0.78,5.24-3.09,6.02-6.02C67.84,34.97,67.84,24,67.84,24 S67.84,13.03,66.52,7.74z"/>
                <polygon fill="#FFFFFF" points="27.2,34.2 44.8,24 27.2,13.8"/>
            </svg>
            <div style="line-height: 1.2;">
                <span style="font-size: 1.15rem; font-weight: 800; color: white; letter-spacing: -0.3px;">YouTube Analytics</span><br>
                <span style="font-size: 0.75rem; color: #AAAAAA; font-weight: 500;">Big Data Platform</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dataset Source Selector in Sidebar
    st.sidebar.subheader("📁 Dataset Source")

    # Load Category Mapping
    category_map, is_custom_category = load_category_mappings()

    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV (e.g. INvideos.csv)",
        type=["csv"],
        help="Upload any Kaggle trending YouTube CSV (INvideos, USvideos, GBvideos, etc.)",
    )

    active_source = None
    source_label = ""

    if uploaded_file is not None:
        active_source = uploaded_file
        source_label = f"Uploaded: {uploaded_file.name}"
    elif DEFAULT_CSV_PATH.exists():
        active_source = DEFAULT_CSV_PATH
        source_label = f"Local File: {DEFAULT_CSV_PATH.name}"

    # If no dataset is available, show onboarding instructions
    if active_source is None:
        render_no_data_screen()
        return

    # Load Data with spinner
    try:
        with st.spinner("Loading and processing dataset..."):
            raw_df, df, meta, summary = load_and_clean_data(active_source, category_map)
    except Exception as e:
        st.error(f"❌ Error loading dataset: {e}")
        st.info(
            "Please ensure the CSV contains required columns: `video_id`, `title`, `channel_title`, `category_id`, `views`."
        )
        return

    st.sidebar.success(f"✓ {source_label} ({len(df):,} clean rows)")

    # Category Mapping Status
    if not is_custom_category:
        st.sidebar.caption(
            "ℹ️ Using built-in standard YouTube categories. Place `IN_category_id.json` in `data/` for region-specific labels."
        )

    # Navigation Menu
    st.sidebar.subheader("🧭 Navigation")
    menu_options = [
        "📊 Overview Dashboard",
        "🎬 Video Analytics",
        "📑 Category Analytics",
        "📢 Channel Analytics",
        "💡 Engagement Analytics",
        "📅 Time-Based Analytics",
        "🔍 Data Explorer & Export",
        "⚡ Big Data Engine (PySpark & Hive)",
    ]
    selected_page = st.sidebar.radio("Go to:", menu_options)

    # Sidebar Interactive Filters
    st.sidebar.subheader("⚙️ Global Filters")

    # Reset Filters Button
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        st.session_state["filter_category"] = "All Categories"
        st.session_state["filter_channel"] = ""
        st.rerun()

    filtered_df = df.copy()

    # Category Filter
    if "category_name" in filtered_df.columns:
        all_categories = ["All Categories"] + sorted(filtered_df["category_name"].unique().tolist())
        selected_category = st.sidebar.selectbox(
            "Filter by Category:",
            all_categories,
            index=0,
            key="filter_category",
        )
        if selected_category != "All Categories":
            filtered_df = filtered_df[filtered_df["category_name"] == selected_category]

    # Channel Search Filter
    channel_search = st.sidebar.text_input(
        "Search Channel Name:",
        placeholder="e.g. T-Series, Sony...",
        key="filter_channel",
    )
    if channel_search.strip():
        filtered_df = filtered_df[
            filtered_df["channel_title"].str.contains(channel_search.strip(), case=False, na=False)
        ]

    # Date Range Filter if available
    if "trending_date_parsed" in filtered_df.columns and filtered_df["trending_date_parsed"].notna().any():
        valid_dates = filtered_df["trending_date_parsed"].dropna()
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
        if min_date < max_date:
            date_range = st.sidebar.date_input(
                "Filter Trending Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_d, end_d = date_range
                filtered_df = filtered_df[
                    (filtered_df["trending_date_parsed"].dt.date >= start_d)
                    & (filtered_df["trending_date_parsed"].dt.date <= end_d)
                ]

    st.sidebar.caption(
        f"Filtered Records: **{len(filtered_df):,}** of **{len(df):,}** ({len(filtered_df)/len(df)*100:.1f}%)"
    )

    # Render Selected Page
    if selected_page == "📊 Overview Dashboard":
        render_overview_page(filtered_df, summary)
    elif selected_page == "🎬 Video Analytics":
        render_video_analytics_page(filtered_df)
    elif selected_page == "📑 Category Analytics":
        render_category_analytics_page(filtered_df)
    elif selected_page == "📢 Channel Analytics":
        render_channel_analytics_page(filtered_df)
    elif selected_page == "💡 Engagement Analytics":
        render_engagement_analytics_page(filtered_df)
    elif selected_page == "📅 Time-Based Analytics":
        render_time_analytics_page(filtered_df)
    elif selected_page == "🔍 Data Explorer & Export":
        render_data_explorer_page(raw_df, df, filtered_df, summary, meta)
    elif selected_page == "⚡ Big Data Engine (PySpark & Hive)":
        render_big_data_page(df, active_source, category_map)


# ==============================================================================
# PAGE 0: Onboarding / No Data Loaded Screen
# ==============================================================================
def render_no_data_screen():
    st.markdown(
        """
        <div style="text-align: center; padding: 45px 20px 25px 20px;">
            <div style="display: flex; justify-content: center; align-items: center; gap: 14px; margin-bottom: 15px;">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 68 48" width="76" height="54">
                    <path fill="#FF0000" d="M66.52,7.74c-0.78-2.93-3.09-5.24-6.02-6.02C55.21,0.4,34,0.4,34,0.4s-21.21,0-26.5,1.32 c-2.94,0.78-5.24,3.09-6.02,6.02C0.16,13.03,0.16,24,0.16,24s0,10.97,1.32,16.26c0.78,2.93,3.08,5.24,6.02,6.02 C12.79,47.6,34,47.6,34,47.6s21.21,0,26.5-1.32c2.93-0.78,5.24-3.09,6.02-6.02C67.84,34.97,67.84,24,67.84,24 S67.84,13.03,66.52,7.74z"/>
                    <polygon fill="#FFFFFF" points="27.2,34.2 44.8,24 27.2,13.8"/>
                </svg>
                <span style="font-size: 2.8rem; font-weight: 900; color: #FFFFFF; letter-spacing: -1.5px; font-family: 'YouTube Sans', 'Roboto', 'Arial Black', sans-serif;">YouTube</span>
            </div>
            <h1 style="color: #FFFFFF; font-size: 2.1rem; font-weight: 700; margin-top: 0; margin-bottom: 8px;">Trending Video Analytics</h1>
            <p style="font-size: 1.15rem; color: #AAAAAA; max-width: 750px; margin: 0 auto 30px auto;">
                Distributed big data analytics powered by Apache Spark, Apache Hive, and Streamlit.
                Analyze large-scale historical trends in viewership, engagement metrics, categories, and channels.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📥 How to Get Started")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            #### Option A: Quick Upload
            1. Use the **Upload CSV** file uploader on the left sidebar.
            2. Choose any regional dataset from Kaggle (`INvideos.csv`, `USvideos.csv`, `GBvideos.csv`, etc.).
            3. The analytics dashboard will load and analyze the dataset immediately!
            """
        )
    with col2:
        st.markdown(
            """
            #### Option B: Place File in `data/` Directory
            1. Download the Kaggle dataset: [Trending YouTube Video Statistics](https://www.kaggle.com/datasets/datasnaek/youtube-new).
            2. Extract `INvideos.csv` into the `data/` directory of this project:
               `youtube-trending-analytics/data/INvideos.csv`
            3. (Optional) Place `IN_category_id.json` in the same directory.
            4. Refresh this page to automatically detect the dataset.
            """
        )

    st.markdown("---")
    st.info(
        "💡 **No YouTube API key required**: This application operates on historical trending logs, making it resilient, privacy-friendly, and ideal for Big Data batch analysis."
    )


# ==============================================================================
# PAGE 1: Overview Dashboard
# ==============================================================================
def render_overview_page(df: pd.DataFrame, summary: dict):
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 68 48" width="36" height="26">
                <path fill="#FF0000" d="M66.52,7.74c-0.78-2.93-3.09-5.24-6.02-6.02C55.21,0.4,34,0.4,34,0.4s-21.21,0-26.5,1.32 c-2.94,0.78-5.24,3.09-6.02,6.02C0.16,13.03,0.16,24,0.16,24s0,10.97,1.32,16.26c0.78,2.93,3.08,5.24,6.02,6.02 C12.79,47.6,34,47.6,34,47.6s21.21,0,26.5-1.32c2.93-0.78,5.24-3.09,6.02-6.02C67.84,34.97,67.84,24,67.84,24 S67.84,13.03,66.52,7.74z"/>
                <polygon fill="#FFFFFF" points="27.2,34.2 44.8,24 27.2,13.8"/>
            </svg>
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 700;">Overview Dashboard</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "Key Performance Indicators (KPIs) and summary aggregates across trending YouTube video records."
    )

    if df.empty:
        st.warning("No records match the current filter criteria. Try resetting the filters.")
        return

    kpis = get_overview_kpis(df)

    # KPI Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Trending Records</div>
                <div class="metric-value">{kpis['total_records']:,}</div>
                <div class="metric-sub">Daily log snapshots</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Unique Videos</div>
                <div class="metric-value">{kpis['unique_videos']:,}</div>
                <div class="metric-sub">Distinct video IDs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Unique Channels</div>
                <div class="metric-value">{kpis['unique_channels']:,}</div>
                <div class="metric-sub">Creators represented</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Views</div>
                <div class="metric-value">{kpis['total_views']:,}</div>
                <div class="metric-sub">Cumulative viewership</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Average Views</div>
                <div class="metric-value">{kpis['avg_views']:,.0f}</div>
                <div class="metric-sub">Per trending record</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Likes</div>
                <div class="metric-value">{kpis['total_likes']:,}</div>
                <div class="metric-sub">{kpis['overall_like_ratio']}% Like-to-View Ratio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c7:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Comments</div>
                <div class="metric-value">{kpis['total_comments']:,}</div>
                <div class="metric-sub">{kpis['overall_comment_ratio']}% Comment-to-View Ratio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c8:
        retention = summary.get("retention_rate_pct", 100.0)
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Data Quality</div>
                <div class="metric-value">{retention}%</div>
                <div class="metric-sub">Records retained post-clean</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Quick Visual Highlights
    col_left, col_right = st.columns([3, 2])
    with col_left:
        top_v = get_top_videos(df, metric="views", top_n=5)
        st.plotly_chart(plot_top_videos(top_v, metric="views", top_n=5), use_container_width=True)

    with col_right:
        cat_df = get_category_analytics(df).head(6)
        st.plotly_chart(
            plot_category_bar(cat_df, metric="total_views", title_suffix="Top 6 Categories"),
            use_container_width=True,
        )


# ==============================================================================
# PAGE 2: Video Analytics
# ==============================================================================
def render_video_analytics_page(df: pd.DataFrame):
    st.markdown("## 🎬 Video Analytics")
    st.markdown(
        "Analyze individual video performance, view rankings, like counts, and engagement leaders."
    )

    if df.empty:
        st.warning("No video records available for the active filters.")
        return

    # Metric Selection Tabs
    rank_metric = st.selectbox(
        "Rank Top Videos By Metric:",
        ["Views", "Likes", "Comments", "Like-to-View Ratio (%)"],
        index=0,
    )
    metric_map = {
        "Views": "views",
        "Likes": "likes",
        "Comments": "comment_count",
        "Like-to-View Ratio (%)": "like_view_ratio",
    }
    selected_col = metric_map[rank_metric]

    top_videos_df = get_top_videos(df, metric=selected_col, top_n=10)

    # Chart
    st.plotly_chart(
        plot_top_videos(top_videos_df, metric=selected_col, top_n=10),
        use_container_width=True,
    )

    # Searchable Interactive Table
    st.markdown("### 🔎 Search & Explore Videos")
    search_query = st.text_input("Filter by video title keyword:", placeholder="Search title...")

    display_df = df.copy()
    if search_query.strip():
        display_df = display_df[
            display_df["title"].str.contains(search_query.strip(), case=False, na=False)
        ]

    cols_to_show = [
        "title",
        "channel_title",
        "category_name",
        "views",
        "likes",
        "comment_count",
        "like_view_ratio",
    ]
    if "dislikes" in display_df.columns:
        cols_to_show.append("dislikes")

    st.dataframe(
        display_df[cols_to_show]
        .rename(
            columns={
                "title": "Title",
                "channel_title": "Channel",
                "category_name": "Category",
                "views": "Views",
                "likes": "Likes",
                "comment_count": "Comments",
                "like_view_ratio": "Like/View %",
                "dislikes": "Dislikes",
            }
        )
        .head(100),
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# PAGE 3: Category Analytics
# ==============================================================================
def render_category_analytics_page(df: pd.DataFrame):
    st.markdown("## 📑 Category Analytics")
    st.markdown(
        "Benchmark viewership, trending frequency, and viewer participation across YouTube content categories."
    )

    if df.empty:
        st.warning("No records available.")
        return

    cat_df = get_category_analytics(df)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            plot_category_bar(cat_df, metric="total_views", title_suffix="Total Views"),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            plot_category_bar(cat_df, metric="trending_records", title_suffix="Trending Frequency"),
            use_container_width=True,
        )

    st.markdown("### 📊 Category Performance Benchmark Table")
    st.dataframe(
        cat_df.rename(
            columns={
                "category_name": "Category",
                "trending_records": "Trending Records",
                "unique_videos": "Unique Videos",
                "total_views": "Total Views",
                "avg_views": "Avg Views",
                "median_views": "Median Views",
                "total_likes": "Total Likes",
                "avg_likes": "Avg Likes",
                "total_comments": "Total Comments",
                "avg_like_ratio": "Avg Like %",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# PAGE 4: Channel Analytics
# ==============================================================================
def render_channel_analytics_page(df: pd.DataFrame):
    st.markdown("## 📢 Channel Analytics")
    st.markdown(
        "Evaluate top content creators by trending volume, cumulative viewership, and average views."
    )

    if df.empty:
        st.warning("No records available.")
        return

    c1, c2 = st.columns([1, 3])
    with c1:
        min_records = st.number_input(
            "Minimum trending records:",
            min_value=1,
            max_value=20,
            value=2,
            help="Filters out one-hit wonders to show channels with consistent trending presence.",
        )
        top_n = st.slider("Number of channels to display:", 5, 30, 15)

    chan_df = get_channel_analytics(df, min_records=min_records, top_n=top_n)

    with c2:
        st.plotly_chart(plot_channel_bar(chan_df, top_n=top_n), use_container_width=True)

    st.markdown("### 🏆 Channel Performance Ranking Table")
    st.dataframe(
        chan_df.rename(
            columns={
                "channel_title": "Channel Name",
                "trending_records": "Trending Records",
                "unique_videos": "Unique Videos",
                "total_views": "Total Views",
                "avg_views_per_record": "Avg Views/Record",
                "total_likes": "Total Likes",
                "avg_likes": "Avg Likes",
                "total_comments": "Total Comments",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ==============================================================================
# PAGE 5: Engagement Analytics
# ==============================================================================
def render_engagement_analytics_page(df: pd.DataFrame):
    st.markdown("## 💡 Engagement Analytics")
    st.markdown(
        "Examine viewer interaction patterns: like-to-view ratios, comment density, and metric correlations."
    )

    st.markdown(
        """
        <div class="caution-box">
            ⚠️ <b>Academic Note on Causation vs. Correlation:</b><br>
            Engagement ratios (like-to-view and comment-to-view) are <i>descriptive metrics</i>. High correlation between views and likes indicates an association, not that getting likes causes a video to accumulate views. Both metrics are influenced by external drivers such as algorithm recommendations, creator popularity, and thumbnail appeal.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.warning("No data available.")
        return

    eng = get_engagement_metrics(df)

    # Correlation Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Views ↔ Likes Corr</div>
                <div class="metric-value">{eng['views_likes_corr']}</div>
                <div class="metric-sub">Pearson correlation (r)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Views ↔ Comments Corr</div>
                <div class="metric-value">{eng['views_comments_corr']}</div>
                <div class="metric-sub">Pearson correlation (r)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Avg Like-to-View</div>
                <div class="metric-value">{eng['avg_like_ratio']}%</div>
                <div class="metric-sub">Mean viewer like rate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Avg Comment-to-View</div>
                <div class="metric-value">{eng['avg_comment_ratio']}%</div>
                <div class="metric-sub">Mean viewer comment rate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            plot_engagement_scatter(df, x_col="views", y_col="likes"),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            plot_engagement_scatter(df, x_col="views", y_col="comment_count"),
            use_container_width=True,
        )


# ==============================================================================
# PAGE 6: Time-Based Analytics
# ==============================================================================
def render_time_analytics_page(df: pd.DataFrame):
    st.markdown("## 📅 Time-Based Analytics")
    st.markdown(
        "Analyze temporal trends: trending timeline, day-of-week frequency, and publishing hour patterns."
    )

    time_data = get_time_based_analytics(df)

    if not time_data["has_trending_date"] and not time_data["has_publish_time"]:
        st.warning(
            "⚠️ Temporal columns (`trending_date` or `publish_time`) are either missing or could not be parsed in this dataset."
        )
        return

    if time_data["has_trending_date"] and not time_data["daily_trends"].empty:
        st.plotly_chart(
            plot_timeline_trends(time_data["daily_trends"]),
            use_container_width=True,
        )

        st.plotly_chart(
            plot_day_of_week(time_data["day_of_week"]),
            use_container_width=True,
        )
    else:
        st.info("ℹ️ Daily trending timeline is not available for this subset.")

    if time_data["has_publish_time"] and not time_data["publish_hour"].empty:
        st.markdown("### ⏰ Video Publishing Hour Patterns (UTC)")
        st.bar_chart(
            time_data["publish_hour"].set_index("hour"),
            color=THEME_COLORS["accent_blue"],
        )
        st.caption("Distribution of hours (0-23 UTC) when trending videos were originally published.")


# ==============================================================================
# PAGE 7: Data Explorer & Export
# ==============================================================================
def render_data_explorer_page(raw_df, df, filtered_df, summary, meta):
    st.markdown("## 🔍 Data Explorer & Cleaning Audit")
    st.markdown(
        "Inspect the raw vs. cleaned dataset schema, missing value statistics, and export cleaned CSV data."
    )

    # Summary Audit Cards
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(
            f"""
            <div class="info-box">
                <b>Cleaning Audit Summary:</b><br>
                • <b>Raw Records Ingested:</b> {summary.get('initial_rows', 0):,}<br>
                • <b>Clean Records Retained:</b> {summary.get('final_rows', 0):,} ({summary.get('retention_rate_pct', 0)}%)<br>
                • <b>Duplicates Removed:</b> {summary.get('duplicates_removed', 0):,}<br>
                • <b>Corrupted/Invalid Views Dropped:</b> {summary.get('rows_with_invalid_views_dropped', 0):,}<br>
                • <b>Detected File Encoding:</b> <code>{meta.get('encoding', 'utf-8')}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        st.plotly_chart(plot_data_retention_pie(summary), use_container_width=True)

    # Missing Values Table
    st.markdown("### 📋 Missing Values Audit")
    missing_data = pd.DataFrame(
        [
            {
                "Column Name": col,
                "Data Type": str(raw_df[col].dtype),
                "Missing Values (Raw)": summary["missing_values_by_column"].get(col, 0),
                "Missing Pct": f"{(summary['missing_values_by_column'].get(col, 0)/len(raw_df)*100):.2f}%",
            }
            for col in raw_df.columns
        ]
    )
    st.dataframe(missing_data, use_container_width=True, hide_index=True)

    # Export Buttons
    st.markdown("### 💾 Export Data")
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        # Download Cleaned Data
        csv_cleaned = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Full Cleaned Dataset (CSV)",
            data=csv_cleaned,
            file_name="youtube_trending_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with d_col2:
        # Download Filtered Data
        csv_filtered = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"📥 Download Current Filtered View ({len(filtered_df):,} rows)",
            data=csv_filtered,
            file_name="youtube_trending_filtered_view.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("### 👁️ Dataset Preview (First 50 Rows)")
    st.dataframe(filtered_df.head(50), use_container_width=True)


# ==============================================================================
# PAGE 8: Big Data Engine (PySpark & Hive)
# ==============================================================================
def render_big_data_page(df, active_source, category_map):
    st.markdown("## ⚡ Big Data Processing Engine: PySpark & Apache Hive")
    st.markdown(
        "Scalable distributed processing with Apache Spark, Spark SQL query execution, and Apache Hive data warehousing."
    )

    tab_spark, tab_hive, tab_arch = st.tabs(
        ["🔥 PySpark Execution", "🐝 Apache Hive Integration", "📐 Big Data Architecture"]
    )

    with tab_spark:
        st.markdown("### Apache Spark Distributed Execution Mode")
        st.markdown(
            "PySpark processes big data using Resilient Distributed Datasets (RDDs) and Catalyst-optimized DataFrames across distributed partitions."
        )

        spark_status = check_spark_environment()

        if not spark_status["is_ready"]:
            st.markdown(
                f"""
                <div class="caution-box">
                    <b>⚠️ PySpark Local Mode Requirement:</b><br>
                    {spark_status['message']}<br><br>
                    <b>Setup Steps to Enable PySpark:</b><br>
                    <pre>{spark_status['setup_guide']}</pre>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.info(
                "💡 **Notice:** The dashboard is currently executing analytics in local mode. If you install Java 11 or 17, clicking the button below will run the distributed SparkSession job on your machine."
            )
        else:
            st.success(f"✓ {spark_status['message']}")

            # Resolve local path for PySpark ingestion (handles both local files and uploaded files)
            def resolve_local_file_path(source) -> Path:
                if isinstance(source, (str, Path)) and Path(source).exists():
                    return Path(source)
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                target_path = DATA_DIR / "uploaded_dataset.csv"
                if hasattr(source, "getbuffer"):
                    with open(target_path, "wb") as f:
                        f.write(source.getbuffer())
                elif hasattr(source, "read"):
                    source.seek(0)
                    with open(target_path, "wb") as f:
                        f.write(source.read())
                    source.seek(0)
                return target_path

            if st.button("🚀 Run Distributed PySpark Job", type="primary"):
                with st.spinner("Starting SparkSession & executing PySpark DAG..."):
                    try:
                        resolved_path = resolve_local_file_path(active_source)
                        spark = get_spark_session()
                        spark_df, spark_metrics = process_with_pyspark(
                            spark, str(resolved_path), category_map
                        )
                        st.session_state["spark_metrics"] = spark_metrics
                        st.session_state["spark_top_videos"] = run_spark_sql(
                            spark,
                            "SELECT title, channel_title, views, likes, comment_count, like_view_ratio FROM trending_videos ORDER BY views DESC LIMIT 10",
                        )
                        st.session_state["spark_cat_summary"] = run_spark_sql(
                            spark,
                            "SELECT category_name, count(*) as trending_records, sum(views) as total_views, round(avg(views), 1) as avg_views FROM trending_videos GROUP BY category_name ORDER BY total_views DESC LIMIT 10",
                        )
                        st.session_state["spark_job_executed"] = True
                    except Exception as e:
                        st.error(f"PySpark job error: {e}")

            if st.session_state.get("spark_job_executed"):
                metrics = st.session_state["spark_metrics"]
                st.success(
                    f"🎉 **Spark job completed in {metrics['spark_execution_time_seconds']}s!** "
                    f"Processed {metrics['clean_record_count']:,} records across {metrics['spark_partitions']} partition(s)."
                )

                # PySpark Metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Raw Ingested Records", f"{metrics['raw_record_count']:,}")
                with m2:
                    st.metric("Clean Spark Records", f"{metrics['clean_record_count']:,}")
                with m3:
                    st.metric("Deduplicated / Dropped", f"{metrics['records_dropped']:,}")
                with m4:
                    st.metric("RDD Partitions", f"{metrics['spark_partitions']}")

                st.markdown("---")
                st.markdown("#### ⚡ Spark SQL Analytics Results")

                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown("**Top 10 Most-Viewed Videos (PySpark Engine)**")
                    st.dataframe(
                        st.session_state["spark_top_videos"],
                        use_container_width=True,
                        hide_index=True,
                    )
                with c_right:
                    st.markdown("**Category Viewership (PySpark Engine)**")
                    st.dataframe(
                        st.session_state["spark_cat_summary"],
                        use_container_width=True,
                        hide_index=True,
                    )

                st.markdown("---")
                st.markdown("#### 💻 Ad-hoc Spark SQL Query Console")
                user_query = st.text_area(
                    "Execute custom SQL on `trending_videos` view:",
                    "SELECT channel_title, count(*) as records, sum(views) as total_views, round(avg(views), 1) as avg_views FROM trending_videos GROUP BY channel_title ORDER BY records DESC LIMIT 10",
                    height=80,
                )
                if st.button("Execute Custom Spark SQL Query"):
                    with st.spinner("Running Spark SQL query..."):
                        try:
                            spark = get_spark_session()
                            custom_res = run_spark_sql(spark, user_query)
                            st.dataframe(custom_res, use_container_width=True, hide_index=True)
                        except Exception as q_err:
                            st.error(f"Query error: {q_err}")

    with tab_hive:
        st.markdown("### Apache Hive Data Warehousing")
        st.markdown(
            "Apache Hive facilitates SQL-based querying on large datasets stored in the Hadoop Distributed File System (HDFS)."
        )

        st.markdown(
            """
            <div class="info-box">
                <b>Environment Status:</b> Standalone Laptop Mode (Hadoop/Hive cluster not directly attached).<br>
                Production HiveQL scripts have been prepared and tested under the <code>hive/</code> directory.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Available HiveQL Scripts")
        hive_dir = Path(__file__).resolve().parent / "hive"
        if hive_dir.exists():
            scripts = list(hive_dir.glob("*.sql"))
            selected_script = st.selectbox("Select HiveQL script to view:", [s.name for s in scripts])
            if selected_script:
                script_path = hive_dir / selected_script
                with open(script_path, "r", encoding="utf-8") as f:
                    content = f.read()
                st.code(content, language="sql")

    with tab_arch:
        st.markdown("### 📐 Big Data Architecture Diagram & Methodology")
        st.markdown(
            """
            ```
            ┌─────────────────────────────────────────────────────────────┐
            │                  Kaggle / YouTube Logs Ingestion            │
            │                  (INvideos.csv, IN_category.json)           │
            └──────────────────────────────┬──────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
            ┌───────────────────────────┐         ┌───────────────────────────┐
            │    Local Laptop Mode      │         │   Hadoop / Big Data Mode  │
            │  (Pandas + Plotly Engine) │         │    (HDFS + Hive + PySpark)│
            ├───────────────────────────┤         ├───────────────────────────┤
            │ • Safe type coercion      │         │ • HDFS distributed blocks │
            │ • Regex date parsing      │         │ • OpenCSVSerde staging    │
            │ • Sub-second rendering    │         │ • ORC columnar storage    │
            │ • No JVM dependency       │         │ • MapReduce / Tez queries │
            └─────────────┬─────────────┘         └─────────────┬─────────────┘
                          │                                     │
                          └───────────────────┬─────────────────┘
                                              ▼
            ┌─────────────────────────────────────────────────────────────┐
            │               Streamlit Interactive Web UI                  │
            │  (KPIs, Top Videos, Category Benchmarks, Engagement Ratios) │
            └─────────────────────────────────────────────────────────────┘
            ```
            """
        )
        st.markdown(
            """
            #### Key Big Data Concepts Applied:
            1. **Batch Ingestion:** Handling semi-structured CSVs with quoted delimiters and Unicode titles.
            2. **Distributed Deduplication:** Removing redundant daily log entries using compound keys (`video_id + trending_date`).
            3. **Safe Mathematical Reductions:** Mitigating zero-division errors during distributed metric calculation (`like_to_view_ratio`).
            4. **Storage Formats:** Comparing row-based Text/CSV storage against Hive columnar formats (ORC) with Snappy compression for 5x-10x query acceleration.
            """
        )


if __name__ == "__main__":
    main()
