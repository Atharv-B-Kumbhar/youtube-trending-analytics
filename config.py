"""
Configuration settings for the YouTube Trending Video Analytics project.
Defines project paths, data validation schemas, UI themes, and PySpark configuration.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_CSV_PATH = DATA_DIR / "INvideos.csv"
DEFAULT_CATEGORY_JSON = DATA_DIR / "IN_category_id.json"

# Core Required Schema
# A file must have at least these columns to run valid analysis
REQUIRED_COLUMNS = [
    "video_id",
    "title",
    "channel_title",
    "category_id",
    "views",
]

# Supported Optional Schema Columns
OPTIONAL_NUMERIC_COLUMNS = [
    "likes",
    "dislikes",
    "comment_count",
]

OPTIONAL_DATE_COLUMNS = [
    "trending_date",
    "publish_time",
]

ALL_EXPECTED_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_NUMERIC_COLUMNS + OPTIONAL_DATE_COLUMNS + [
    "tags",
    "thumbnail_link",
    "comments_disabled",
    "ratings_disabled",
    "video_error_or_removed",
    "description",
]

# Built-in YouTube Standard Category ID Mapping (ISO / YouTube Data API standard)
# Used as high-fidelity fallback if IN_category_id.json is not present
STANDARD_CATEGORY_MAP = {
    1: "Film & Animation",
    2: "Autos & Vehicles",
    10: "Music",
    15: "Pets & Animals",
    17: "Sports",
    18: "Short Movies",
    19: "Travel & Events",
    20: "Gaming",
    21: "Videoblogging",
    22: "People & Blogs",
    23: "Comedy",
    24: "Entertainment",
    25: "News & Politics",
    26: "Howto & Style",
    27: "Education",
    28: "Science & Technology",
    29: "Nonprofits & Activism",
    30: "Movies",
    31: "Anime/Animation",
    32: "Action/Adventure",
    33: "Classics",
    34: "Comedy",
    35: "Documentary",
    36: "Drama",
    37: "Family",
    38: "Foreign",
    39: "Horror",
    40: "Sci-Fi/Fantasy",
    41: "Thriller",
    42: "Shorts",
    43: "Shows",
    44: "Trailers",
}

# Theme Colors (YouTube Inspired)
THEME_COLORS = {
    "primary_red": "#FF0000",
    "dark_red": "#CC0000",
    "dark_bg": "#0F0F0F",
    "card_bg": "#1E1E1E",
    "secondary_bg": "#282828",
    "border_color": "#3E3E3E",
    "text_primary": "#FFFFFF",
    "text_secondary": "#AAAAAA",
    "accent_blue": "#3EA6FF",
    "accent_green": "#2BA640",
    "accent_yellow": "#FFD600",
    "accent_purple": "#A855F7",
}

# PySpark Configuration
SPARK_CONFIG = {
    "app_name": "YouTubeTrendingAnalytics",
    "master": "local[*]",
    "driver_memory": "2g",
    "sql_shuffle_partitions": "4",
}
