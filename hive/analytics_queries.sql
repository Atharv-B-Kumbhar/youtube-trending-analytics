-- ============================================================================
-- Apache Hive Script: Analytical SQL Queries
-- Project: YouTube Trending Video Analytics Using Big Data Technologies
-- ============================================================================

USE youtube_analytics;

-- ============================================================================
-- QUERY 1: Overview Big Data Aggregations
-- ============================================================================
SELECT 
    COUNT(*) AS total_trending_records,
    COUNT(DISTINCT video_id) AS unique_videos,
    COUNT(DISTINCT channel_title) AS unique_channels,
    SUM(views) AS total_views,
    SUM(likes) AS total_likes,
    SUM(comment_count) AS total_comments,
    ROUND(AVG(views), 2) AS avg_views_per_record
FROM cleaned_youtube_trending;


-- ============================================================================
-- QUERY 2: Top 10 Most-Viewed Trending Videos
-- (Deduplicated using subquery to take the peak view count for each video)
-- ============================================================================
SELECT 
    title,
    channel_title,
    category_name,
    max_views,
    likes,
    comment_count
FROM (
    SELECT 
        title,
        channel_title,
        category_name,
        views AS max_views,
        likes,
        comment_count,
        ROW_NUMBER() OVER (PARTITION BY video_id ORDER BY views DESC) as rank
    FROM cleaned_youtube_trending
) ranked
WHERE rank = 1
ORDER BY max_views DESC
LIMIT 10;


-- ============================================================================
-- QUERY 3: Top 10 Most-Liked Videos
-- ============================================================================
SELECT 
    title,
    channel_title,
    category_name,
    views,
    likes,
    like_view_ratio
FROM (
    SELECT 
        title,
        channel_title,
        category_name,
        views,
        likes,
        like_view_ratio,
        ROW_NUMBER() OVER (PARTITION BY video_id ORDER BY likes DESC) as rank
    FROM cleaned_youtube_trending
) ranked
WHERE rank = 1
ORDER BY likes DESC
LIMIT 10;


-- ============================================================================
-- QUERY 4: Category Performance Benchmark
-- Total viewership, average views, and trending volume per category
-- ============================================================================
SELECT 
    category_name,
    COUNT(*) AS trending_records,
    COUNT(DISTINCT video_id) AS unique_videos,
    SUM(views) AS total_views,
    ROUND(AVG(views), 2) AS avg_views_per_record,
    ROUND(AVG(likes), 2) AS avg_likes,
    ROUND(AVG(comment_count), 2) AS avg_comments,
    ROUND(AVG(like_view_ratio), 2) AS avg_like_ratio_pct
FROM cleaned_youtube_trending
GROUP BY category_name
ORDER BY total_views DESC;


-- ============================================================================
-- QUERY 5: Top 15 Channels with Most Trending Records (Trending Frequency)
-- ============================================================================
SELECT 
    channel_title,
    COUNT(*) AS trending_records,
    COUNT(DISTINCT video_id) AS unique_videos,
    SUM(views) AS total_views,
    ROUND(AVG(views), 2) AS avg_views_per_record
FROM cleaned_youtube_trending
GROUP BY channel_title
ORDER BY trending_records DESC
LIMIT 15;


-- ============================================================================
-- QUERY 6: Top 10 Channels by Average Views (Minimum 5 Trending Records)
-- ============================================================================
SELECT 
    channel_title,
    COUNT(*) AS trending_records,
    SUM(views) AS total_views,
    ROUND(AVG(views), 2) AS avg_views_per_record
FROM cleaned_youtube_trending
GROUP BY channel_title
HAVING COUNT(*) >= 5
ORDER BY avg_views_per_record DESC
LIMIT 10;


-- ============================================================================
-- QUERY 7: Top Videos with Highest Engagement (Like-to-View Ratio)
-- Filtered for significant viewership (> 50,000 views) to avoid noise
-- ============================================================================
SELECT 
    title,
    channel_title,
    category_name,
    views,
    likes,
    like_view_ratio
FROM cleaned_youtube_trending
WHERE views >= 50000
ORDER BY like_view_ratio DESC
LIMIT 10;


-- ============================================================================
-- QUERY 8: Date-Based Trending Trends Timeline
-- Daily count of trending videos and total daily viewership
-- ============================================================================
SELECT 
    trending_date,
    COUNT(*) AS daily_trending_videos,
    SUM(views) AS daily_total_views,
    ROUND(AVG(views), 2) AS daily_avg_views
FROM cleaned_youtube_trending
WHERE trending_date IS NOT NULL
GROUP BY trending_date
ORDER BY trending_date ASC
LIMIT 30;
