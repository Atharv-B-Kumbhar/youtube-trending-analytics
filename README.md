# YouTube Trending Video Analytics Using Big Data Technologies

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySpark](https://img.shields.io/badge/PySpark-4.2-orange)
![Apache_Hive](https://img.shields.io/badge/Apache_Hive-3.x-yellow)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-red)
![Plotly](https://img.shields.io/badge/Plotly-Interactive-brightgreen)
![Tests](https://img.shields.io/badge/PyTest-23%20Passed-success)

A complete Big Data Analytics platform that analyzes historical YouTube trending video data (specifically India `INvideos.csv`, with support for all regions). Built with **Python**, **PySpark**, **Apache Hive**, and **Streamlit**.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Technologies Used & Rationale](#2-technologies-used--rationale)
3. [Project Structure](#3-project-structure)
4. [Dataset Download & Placement](#4-dataset-download--placement)
5. [Step-by-Step Installation & Setup](#5-step-by-step-installation--setup)
6. [Running the Streamlit Dashboard](#6-running-the-streamlit-dashboard)
7. [Running Standalone PySpark Batch Jobs](#7-running-standalone-pyspark-batch-jobs)
8. [How PySpark is Used](#8-how-pyspark-is-used)
9. [How to Run Apache HiveQL Scripts](#9-how-to-run-apache-hiveql-scripts)
10. [Running Automated Tests](#10-running-automated-tests)
11. [Troubleshooting & Common Errors](#11-troubleshooting--common-errors)
12. [Limitations of Historical Trending Data](#12-limitations-of-historical-trending-data)
13. [College Faculty Viva & Presentation Script](#13-college-faculty-viva--presentation-script)

---

## 1. Project Overview

This project analyzes historical YouTube trending video patterns to extract actionable insights on:
- **Viewership & Popularity:** Most viewed, liked, and commented trending videos.
- **Category Benchmarks:** Distribution of viral content across Entertainment, Music, News, Tech, etc.
- **Creator Consistency:** Channels appearing most frequently on the daily trending charts.
- **Engagement Ratios:** Like-to-view and comment-to-view participation metrics without zero-division errors.
- **Temporal Trends:** Trending patterns across months, days of the week, and publishing hours.
- **Big Data Engineering:** Deduplicating daily snapshots, handling missing columns, and providing HiveQL warehouse schemas and PySpark distributed execution.

**No YouTube API key is required.** The project operates directly on the Kaggle historical dataset.

---

## 2. Technologies Used & Rationale

| Technology | Purpose | Why We Used It |
| :--- | :--- | :--- |
| **Python** | Application logic & pipeline | Simple, expressive, and standard for data science and big data scripting. |
| **PySpark** | Distributed data processing | Processes large datasets in-memory across distributed partitions with Catalyst optimization. |
| **Apache Hive** | SQL-based data warehousing | Enables SQL queries (HiveQL) over HDFS using external staging tables and managed ORC storage. |
| **Streamlit** | Interactive web dashboard | Renders a modern, responsive UI in pure Python with zero front-end setup. |
| **Plotly** | Data visualization | Interactive zooming, tooltips, and responsive charts themed with YouTube dark aesthetics. |
| **PyTest** | Automated unit testing | Verifies data cleaning, edge cases (zero views, corrupted strings), and aggregations. |

---

## 3. Project Structure

```
youtube-trending-analytics/
├── app.py                      # Main Streamlit web application
├── run_spark.py                # Standalone PySpark batch job execution CLI
├── config.py                   # Configuration constants, schemas, and color palette
├── requirements.txt            # Python dependencies
├── README.md                   # Complete beginner-friendly documentation
├── .gitignore                  # Git ignore rules for virtualenvs and data files
├── data/
│   ├── README.md               # Dataset download instructions
│   └── INvideos.csv            # (Place Kaggle dataset here)
├── src/
│   ├── __init__.py             # Package initializer
│   ├── data_loader.py          # CSV and JSON loader with encoding fallbacks
│   ├── data_cleaner.py         # Data cleaning, deduplication, and audit summary
│   ├── analytics.py            # KPI calculations, rankings, and statistical metrics
│   ├── pyspark_processor.py    # PySpark DAG, Spark SQL, and diagnostics
│   └── visualizations.py       # Reusable Plotly charts with YouTube dark styling
├── hive/
│   ├── create_database.sql     # HiveQL: Database creation
│   ├── create_tables.sql       # HiveQL: External staging and Managed ORC tables
│   ├── load_data.sql           # HiveQL: Data ingestion and ETL transformation
│   └── analytics_queries.sql   # HiveQL: 8 Production analytical queries
├── tests/
│   ├── __init__.py             # Test suite initializer
│   ├── test_data_loader.py     # Tests for CSV parser and schema validator
│   ├── test_data_cleaner.py    # Tests for deduplication, zero views, and cleaning
│   └── test_analytics.py       # Tests for KPIs, category, channel, and time metrics
└── docs/
    └── methodology.md          # Big Data architecture, 5 V's, and college viva guide
```

---

## 4. Dataset Download & Placement

### Step 1: Download from Kaggle
1. Visit the Kaggle dataset page:  
   👉 **[Trending YouTube Video Statistics (Kaggle)](https://www.kaggle.com/datasets/datasnaek/youtube-new)**
2. Click **Download (Archive.zip)** (size is approx. 200 MB compressed).

### Step 2: Extract & Place the Files
Extract the zip file and copy `INvideos.csv` into the `data/` folder:

```
youtube-trending-analytics/
└── data/
    ├── README.md
    ├── INvideos.csv            <-- (Place INvideos.csv here)
    └── IN_category_id.json     <-- (Optional: Place category mapping JSON here)
```

> **Note:** The application also supports uploading `INvideos.csv` (or any other regional file like `USvideos.csv`, `GBvideos.csv`, etc.) directly via the **Upload CSV** button in the dashboard sidebar.

---

## 5. Step-by-Step Installation & Setup

### Windows PowerShell

1. **Open PowerShell** and navigate to your project folder:
   ```powershell
   cd "C:\Users\atharv\Desktop\SEM VII Projects\BDA\youtube-trending-analytics"
   ```

2. **(Optional) Create and activate a Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(If you see an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

### macOS / Linux Terminal

```bash
cd youtube-trending-analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 6. Running the Streamlit Dashboard

Launch the interactive dashboard with a single command:

```powershell
python -m streamlit run app.py
```

Or simply:
```powershell
streamlit run app.py
```

The browser will open automatically at:
👉 **`http://localhost:8501`**

Inside the dashboard:
1. Upload `INvideos.csv` or place it in `data/`.
2. Navigate to **⚡ Big Data Engine (PySpark & Hive)** on the left sidebar.
3. Click **🚀 Run Distributed PySpark Job** to trigger the distributed Spark pipeline and execute ad-hoc Spark SQL queries directly in the UI.

---

## 7. Running Standalone PySpark Batch Jobs

You can also run PySpark directly as a standalone batch job in PowerShell or Command Prompt:

```powershell
python run_spark.py
```

Or specify a custom CSV path:
```powershell
python run_spark.py --input data/INvideos.csv
```

### What this job does:
- Starts a local multi-core SparkSession (`local[*]`).
- Ingests the raw CSV dataset across distributed Spark partitions.
- Executes distributed deduplication and cleans invalid view counts.
- Computes safe engagement ratios with Spark's conditional functions.
- Registers an in-memory SQL view (`trending_videos`).
- Executes 3 analytical Spark SQL queries (Top Videos, Category Benchmarks, Channel Rankings) and prints execution metrics.


## 8. How PySpark is Used

The project includes an Apache Spark processing engine located in [`src/pyspark_processor.py`](src/pyspark_processor.py).

### How it works:
1. **Local Mode:** Configures `local[*]` to leverage all CPU cores on a personal laptop without needing a cloud cluster.
2. **Resilient Ingestion:** Uses Spark's DataFrame reader with multi-line quote escaping.
3. **Distributed Deduplication:** Executes `.dropDuplicates(['video_id', 'trending_date'])` across partitions.
4. **Conditional Expressions:** Computes engagement metrics using `F.when(col("views") > 0, ...)` to guarantee zero-division safety.
5. **Spark SQL Engine:** Registers the cleaned DataFrame as an in-memory SQL view (`trending_videos`) allowing ad-hoc SQL querying directly in the dashboard.

### Java Requirement for PySpark:
PySpark runs on the Java Virtual Machine (JVM). Since Microsoft OpenJDK 17 is installed on your system, the application auto-detects `JAVA_HOME` and connects immediately.

---

## 9. How to Run Apache HiveQL Scripts

The `hive/` directory contains standard HiveQL scripts ready for execution on any Apache Hadoop/Hive cluster:

1. **`hive/create_database.sql`**: Initializes the `youtube_analytics` database.
2. **`hive/create_tables.sql`**: Defines an **External Table** (`raw_youtube_trending`) using `OpenCSVSerde` for staging, and an **Optimized Managed Table** (`cleaned_youtube_trending`) stored as **ORC with Snappy compression**.
3. **`hive/load_data.sql`**: Loads the CSV from HDFS and performs the ETL transformation.
4. **`hive/analytics_queries.sql`**: Runs 8 analytics queries (KPIs, Top Videos, Category Benchmarks, Channel Rankings, Engagement Ratios).

### Executing on a Hadoop/Hive Cluster:

```bash
# 1. Upload CSV to HDFS
hdfs dfs -mkdir -p /data/youtube/raw
hdfs dfs -put INvideos.csv /data/youtube/raw/

# 2. Run the HiveQL scripts using the Beeline or Hive CLI
hive -f hive/create_database.sql
hive -f hive/create_tables.sql
hive -f hive/load_data.sql
hive -f hive/analytics_queries.sql
```

---

## 10. Running Automated Tests

Run the full automated test suite using `pytest`:

```powershell
python -m pytest tests/ -v
```

### Verified Test Coverage:
- `tests/test_data_loader.py`: CSV parsing, UTF-8/Unicode character handling, missing column validation, category JSON fallback.
- `tests/test_data_cleaner.py`: Deduplication on `(video_id, trending_date)`, non-numeric view handling, zero-view division protection, date parsing.
- `tests/test_analytics.py`: KPI calculation, category aggregations, channel performance rankings, engagement distributions.
- `tests/test_pyspark.py`: SparkSession creation, distributed DataFrame deduplication, Spark SQL view querying.

All **23 test cases pass cleanly**.

---

## 11. Troubleshooting & Common Errors

### Q1: "java is not recognized as an internal or external command"
- **Reason:** Windows terminals opened before OpenJDK was installed haven't reloaded the updated PATH.
- **Solution:** Our code includes auto-detection for OpenJDK. If running manually outside Python, simply open a new PowerShell terminal or set:
  ```powershell
  $env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot"
  $env:Path = "$env:JAVA_HOME\bin;" + $env:Path
  ```

---

## 12. Limitations of Historical Trending Data

When presenting this project to your faculty, note these important academic limitations:
1. **Algorithmic Selection:** The dataset only contains videos that made it onto the *Trending Tab*. It is not a random sample of all YouTube videos.
2. **Regional Specificity:** Trending criteria differ by geographic region and language preferences.
3. **Correlation vs. Causation:** High correlation between likes and views does not prove that likes cause views; both reflect audience reach and external sharing.
4. **Snapshot Gaps:** A video may trend for 1 day, drop off, and return later; daily logs capture discrete snapshots rather than continuous view curves.

---

## 13. College Faculty Viva & Presentation Script

Use this short script when presenting your project to the evaluator or faculty:

> *"Good morning, Professors. Our project is titled **'YouTube Trending Video Analytics Using Big Data Technologies'**.*  
>  
> *The objective of this project is to analyze historical YouTube trending data to discover patterns in viewership, audience engagement, content categories, and creator performance.*  
>  
> *From a Big Data perspective, we tackled four key challenges:*  
> *1. **Data Ingestion & Cleaning:** Historical logs have schema variations, missing values, and Unicode titles. We built a data cleaner that removes redundant daily snapshots using composite keys `(video_id + trending_date)` and safely handles zero-division errors when calculating engagement ratios.*  
> *2. **Distributed Processing with PySpark:** We implemented an Apache Spark module that leverages in-memory RDDs, Catalyst optimization, and Spark SQL temporary views.*  
> *3. **Data Warehousing with Apache Hive:** We authored production HiveQL scripts utilizing external staging tables with OpenCSVSerde and optimized managed tables using columnar ORC storage with Snappy compression.*  
> *4. **Interactive Dashboard:** We built an interactive Streamlit dashboard featuring 8 analytical modules: Overview KPIs, Video Rankings, Category Benchmarks, Channel Performance, Engagement Correlations, Time-Based Analytics, a Data Explorer with CSV export, and a Big Data Engine console.*  
>  
> *The project is fully modular, includes 23 passing automated unit tests, and runs locally without requiring expensive cloud infrastructure."*
