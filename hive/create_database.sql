-- ============================================================================
-- Apache Hive Script: Database Initialization
-- Project: YouTube Trending Video Analytics Using Big Data Technologies
-- ============================================================================

-- Create dedicated database for YouTube Analytics
CREATE DATABASE IF NOT EXISTS youtube_analytics
COMMENT 'Database for historical YouTube trending video data warehousing'
LOCATION '/user/hive/warehouse/youtube_analytics.db';

-- Set current database context
USE youtube_analytics;

-- Verify database creation
DESCRIBE DATABASE EXTENDED youtube_analytics;
