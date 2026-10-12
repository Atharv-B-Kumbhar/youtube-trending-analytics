-- ============================================================================
-- Apache Hive Script: Data Ingestion and Transformation
-- Project: YouTube Trending Video Analytics Using Big Data Technologies
-- ============================================================================

USE youtube_analytics;

-- Step 1: Load raw CSV into staging table
-- If running on local cluster with file in /tmp/INvideos.csv:
-- LOAD DATA LOCAL INPATH '/tmp/INvideos.csv' OVERWRITE INTO TABLE raw_youtube_trending;

-- Or if uploading via HDFS CLI:
-- hdfs dfs -mkdir -p /data/youtube/raw
-- hdfs dfs -put INvideos.csv /data/youtube/raw/

-- Step 2: Populate Category Dimension Table
INSERT OVERWRITE TABLE dim_youtube_category VALUES
(1, 'Film & Animation'),
(2, 'Autos & Vehicles'),
(10, 'Music'),
(15, 'Pets & Animals'),
(17, 'Sports'),
(18, 'Short Movies'),
(19, 'Travel & Events'),
(20, 'Gaming'),
(21, 'Videoblogging'),
(22, 'People & Blogs'),
(23, 'Comedy'),
(24, 'Entertainment'),
(25, 'News & Politics'),
(26, 'Howto & Style'),
(27, 'Education'),
(28, 'Science & Technology'),
(29, 'Nonprofits & Activism'),
(30, 'Movies'),
(43, 'Shows'),
(44, 'Trailers');

-- Step 3: ETL Transformation - Clean, Deduplicate, Enrich, and Store in ORC
INSERT OVERWRITE TABLE cleaned_youtube_trending
SELECT
    r.video_id,
    r.trending_date,
    trim(r.title) AS title,
    trim(r.channel_title) AS channel_title,
    cast(r.category_id AS INT) AS category_id,
    COALESCE(c.category_name, concat('Category ', r.category_id)) AS category_name,
    cast(r.publish_time AS TIMESTAMP) AS publish_time,
    cast(r.views AS BIGINT) AS views,
    COALESCE(cast(r.likes AS BIGINT), 0) AS likes,
    COALESCE(cast(r.dislikes AS BIGINT), 0) AS dislikes,
    COALESCE(cast(r.comment_count AS BIGINT), 0) AS comment_count,
    -- Safe like-to-view ratio (avoiding zero division)
    CASE 
        WHEN cast(r.views AS BIGINT) > 0 
        THEN round((cast(r.likes AS BIGINT) / cast(r.views AS BIGINT)) * 100.0, 4)
        ELSE 0.0 
    END AS like_view_ratio,
    -- Safe comment-to-view ratio
    CASE 
        WHEN cast(r.views AS BIGINT) > 0 
        THEN round((cast(r.comment_count AS BIGINT) / cast(r.views AS BIGINT)) * 100.0, 4)
        ELSE 0.0 
    END AS comment_view_ratio
FROM raw_youtube_trending r
LEFT JOIN dim_youtube_category c ON cast(r.category_id AS INT) = c.category_id
WHERE r.video_id IS NOT NULL 
  AND r.video_id != '#NAME?'
  AND cast(r.views AS BIGINT) >= 0;
