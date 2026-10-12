# YouTube Trending Dataset Instructions

This directory (`data/`) is where the Kaggle YouTube Trending Video dataset files should be placed.

---

## 1. Where to Download

Download the historical dataset from Kaggle:
👉 **URL**: [Trending YouTube Video Statistics (Kaggle)](https://www.kaggle.com/datasets/datasnaek/youtube-new)

---

## 2. Files to Place Here

From the downloaded zip archive, extract and place the following two files into this `data/` directory:

1. **`INvideos.csv`** (Required for primary analysis)
   - Contains historical trending video records for YouTube India.
   - Primary columns: `video_id`, `trending_date`, `title`, `channel_title`, `category_id`, `publish_time`, `tags`, `views`, `likes`, `dislikes`, `comment_count`, etc.

2. **`IN_category_id.json`** (Recommended)
   - Contains the category ID to category title mappings (e.g., `10` -> `Music`, `23` -> `Comedy`, `24` -> `Entertainment`).
   - If not present, the application will automatically fall back to YouTube standard category mappings defined in `config.py`.

---

## 3. Compatibility with Other Regional Datasets

This application also supports other regions from the same Kaggle dataset:
- `USvideos.csv` / `US_category_id.json` (United States)
- `GBvideos.csv` / `GB_category_id.json` (Great Britain)
- `CAvideos.csv` / `CA_category_id.json` (Canada)
- `DEvideos.csv`, `FRvideos.csv`, `JPvideos.csv`, etc.

You can also upload any of these files directly via the **Upload Dataset** feature in the Streamlit web dashboard.
