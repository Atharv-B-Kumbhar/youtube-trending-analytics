-- ============================================================================
-- Apache Hive Script: Table Creation (External & Managed ORC)
-- Project: YouTube Trending Video Analytics Using Big Data Technologies
-- ============================================================================

USE youtube_analytics;

-- 1. External Staging Table for Raw CSV Ingestion
-- Uses CSV SerDe to handle quoted strings containing commas in titles/tags
DROP TABLE IF EXISTS raw_youtube_trending;

CREATE EXTERNAL TABLE IF NOT EXISTS raw_youtube_trending (
    video_id                STRING,
    trending_date           STRING,
    title                   STRING,
    channel_title           STRING,
    category_id             INT,
    publish_time            STRING,
    tags                    STRING,
    views                   BIGINT,
    likes                   BIGINT,
    dislikes                BIGINT,
    comment_count           BIGINT,
    thumbnail_link          STRING,
    comments_disabled       BOOLEAN,
    ratings_disabled        BOOLEAN,
    video_error_or_removed  BOOLEAN,
    description             STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
    "separatorChar" = ",",
    "quoteChar"     = "\"",
    "escapeChar"    = "\\"
)
STORED AS TEXTFILE
LOCATION '/data/youtube/raw/'
TBLPROPERTIES ("skip.header.line.count"="1");


-- 2. Optimized Managed Analytics Table (ORC Storage with Snappy Compression)
-- Cleaned, deduplicated, and typed for high-performance Big Data queries
DROP TABLE IF EXISTS cleaned_youtube_trending;

CREATE TABLE IF NOT EXISTS cleaned_youtube_trending (
    video_id                STRING,
    trending_date           STRING,
    title                   STRING,
    channel_title           STRING,
    category_id             INT,
    category_name           STRING,
    publish_time            TIMESTAMP,
    views                   BIGINT,
    likes                   BIGINT,
    dislikes                BIGINT,
    comment_count           BIGINT,
    like_view_ratio         DOUBLE,
    comment_view_ratio      DOUBLE
)
STORED AS ORC
TBLPROPERTIES (
    "orc.compress"="SNAPPY",
    "transactional"="false"
);


-- 3. Dimension Table: YouTube Category Reference Mapping
DROP TABLE IF EXISTS dim_youtube_category;

CREATE TABLE IF NOT EXISTS dim_youtube_category (
    category_id             INT,
    category_name           STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE;
