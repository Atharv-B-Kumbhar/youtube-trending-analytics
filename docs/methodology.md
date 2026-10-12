# Big Data Analytics Methodology & Architecture

**Project Title:** YouTube Trending Video Analytics Using Big Data Technologies  
**Subject:** Big Data Analytics (BDA) / Data Engineering  
**Academic Context:** College Mini-Project / Semester Project

---

## 1. Executive Summary

YouTube represents one of the largest video-sharing platforms globally, generating massive quantities of unstructured and semi-structured interaction logs daily. Understanding which videos trend, what factors drive engagement, and how viewership distributes across categories and creators is a quintessential Big Data problem.

This project implements an end-to-end Big Data analytical pipeline utilizing:
- **PySpark** for distributed in-memory data processing, schema enforcement, and deduplication.
- **Apache Hive (HiveQL)** for scalable SQL-based data warehousing over HDFS.
- **Streamlit & Plotly** for a modern, responsive web dashboard with zero cloud-cost local deployment.

---

## 2. Big Data Characteristics (The 5 V's)

| Dimension | Description in YouTube Trending Context |
| :--- | :--- |
| **Volume** | Millions of daily interaction logs across dozens of international regions. Daily snapshots accumulate into gigabytes/terabytes over time. |
| **Velocity** | Videos trend dynamically with snapshot intervals capturing viral growth within hours. |
| **Variety** | Semi-structured CSV logs containing unstructured text (titles, descriptions, Unicode regional scripts), integers (views, likes), booleans, and ISO timestamps. |
| **Veracity** | Inconsistent schema (optional dislikes column), missing values, negative counts from log anomalies, corrupted characters, and duplicate daily records. |
| **Value** | Actionable insights for digital marketers, content creators, and media houses to optimize video publishing times, content categories, and engagement. |

---

## 3. System Architecture & Data Flow

```
                      +---------------------------------------+
                      |         Kaggle Historical Logs        |
                      |    (INvideos.csv + IN_category.json)  |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |       Raw Data Validation & Audit     |
                      |  - Verify required columns            |
                      |  - Unicode encoding detection         |
                      +-------------------+-------------------+
                                          |
                  +-----------------------+-----------------------+
                  |                                               |
                  v                                               v
+-----------------------------------+   +-----------------------------------+
|      PySpark Distributed DAG      |   |       Apache Hive Warehouse       |
| - DataFrame Catalyst Optimizer    |   | - External CSV Staging Table      |
| - DropDuplicates(video_id, date)  |   | - OpenCSVSerde Parser             |
| - Zero-division safe ratios       |   | - Managed ORC Table (Snappy)      |
| - Spark SQL In-Memory Views       |   | - Analytical HiveQL Aggregations  |
+-----------------+-----------------+   +-----------------+-----------------+
                  |                                       |
                  +-------------------+-------------------+
                                      v
                      +---------------------------------------+
                      |        Interactive Presentation       |
                      |  - Streamlit YouTube-Themed Dashboard |
                      |  - Interactive Plotly Visualizations  |
                      |  - On-Demand CSV Filtering & Export   |
                      +---------------------------------------+
```

---

## 4. Why Big Data Technologies?

### 4.1 PySpark vs. Traditional Single-Node Pandas
- **Memory Limitations:** Pandas requires the entire dataset to reside in RAM as a contiguous memory block. For multi-gigabyte or streaming datasets, single-machine Pandas encounters `OutOfMemoryError`.
- **In-Memory Distributed Computing:** Apache Spark divides data into partitions across multiple cores or nodes. The **Resilient Distributed Dataset (RDD)** abstraction allows fault-tolerant parallel computation.
- **Catalyst Optimizer:** Spark SQL converts queries into optimized logical and physical execution plans, pushing down projections and filters before loading data.

### 4.2 Apache Hive vs. Traditional Relational Databases (RDBMS)
- **Scale:** RDBMS (such as MySQL or PostgreSQL) are optimized for transactional ACID operations (OLTP) and struggle when table sizes exceed hundreds of gigabytes.
- **Schema-on-Read:** Apache Hive does not verify schema upon writing data to disk; it applies schema when reading from HDFS, allowing instant ingestion of raw log files.
- **Columnar Storage (ORC):** Optimized Row Columnar (ORC) format groups columns together, offering 75%+ compression and enabling Hive queries to read only the specific columns requested in a `SELECT` statement (avoiding full table scans).

---

## 5. Data Cleaning & Engineering Logic

### 5.1 Deduplication Strategy
A single viral video often trends across multiple consecutive days. In raw daily snapshot logs:
- Exact duplicate records logged on the same calendar day are redundant noise.
- **Rule:** Deduplicate using the composite primary key `(video_id, trending_date)`.
- For lifetime aggregate rankings (e.g., Top 10 Most-Viewed Videos), deduplicate strictly on `video_id`, retaining the record with the maximum view count.

### 5.2 Handling Zero-View Division Safely
Engagement ratios measure audience participation:
$$\text{Like-to-View Ratio (\%)} = \left( \frac{\text{likes}}{\text{views}} \right) \times 100$$
$$\text{Comment-to-View Ratio (\%)} = \left( \frac{\text{comment\_count}}{\text{views}} \right) \times 100$$

If $\text{views} = 0$, direct arithmetic causes a runtime `ZeroDivisionError` in Python or produces `NaN` / `NULL` in SQL engines.  
**Resolution:** Use conditional expressions:
- In Python/Pandas: `((df['likes'] / df['views'].replace(0, np.nan)) * 100).fillna(0.0)`
- In PySpark: `F.when(F.col("views") > 0, (F.col("likes") / F.col("views")) * 100).otherwise(0.0)`
- In HiveQL: `CASE WHEN views > 0 THEN round((likes / views) * 100.0, 4) ELSE 0.0 END`

### 5.3 Causation vs. Correlation
In engagement analysis, high Pearson correlation ($r$) between views and likes is often misinterpreted as causation. Statistically, engagement ratios are **descriptive metrics**. Both views and likes are co-dependent on external latent variables (creator subscriber count, external social media shares, and YouTube recommendation algorithms).

---

## 6. College Viva / Examination Questions & Answers

**Q1: What is the difference between an External Table and a Managed Table in Hive?**  
*Answer:* In a Managed Table, Hive owns both the table metadata and the underlying HDFS data files; executing `DROP TABLE` deletes both. In an External Table (defined with the `EXTERNAL` keyword and a `LOCATION`), Hive only manages the metadata; dropping the table leaves the underlying data files in HDFS intact.

**Q2: Why did you use ORC format with Snappy compression in Hive?**  
*Answer:* ORC (Optimized Row Columnar) stores data by column rather than by row. When running analytical queries (e.g., `SUM(views)` by `category_id`), Hive reads only the two relevant columns, avoiding disk I/O on unneeded columns (like titles or descriptions). Snappy compression provides fast decompression with minimal CPU overhead.

**Q3: How does PySpark handle fault tolerance?**  
*Answer:* PySpark uses lineage graphs (Directed Acyclic Graphs or DAGs). If a worker node crashes and a partition is lost, Spark does not need to restart the entire job; it simply recomputes that specific partition by replaying the transformations recorded in the DAG lineage.

**Q4: How did you handle schema variations across different regional CSVs?**  
*Answer:* In our `data_cleaner.py` and `data_loader.py`, we implement dynamic column introspection. We validate mandatory columns (`video_id`, `title`, `views`, etc.) and dynamically detect optional columns like `dislikes` and `publish_time`, setting sensible defaults (such as zero or null) if an optional column is omitted.
