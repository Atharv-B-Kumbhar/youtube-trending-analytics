"""
Unit tests for data_loader module.
Tests CSV parsing, schema validation, and Category JSON mapping fallback.
"""

import io
import json
import pandas as pd
import pytest

from config import STANDARD_CATEGORY_MAP
from src.data_loader import load_category_mappings, load_csv_data, validate_schema


def test_validate_schema_valid():
    df = pd.DataFrame({
        "video_id": ["v1"],
        "title": ["Test Video"],
        "channel_title": ["Test Channel"],
        "category_id": [10],
        "views": [1000],
    })
    is_valid, missing, present, msg = validate_schema(df)
    assert is_valid is True
    assert len(missing) == 0
    assert "video_id" in present


def test_validate_schema_missing_columns():
    df = pd.DataFrame({
        "video_id": ["v1"],
        "title": ["Test Video"],
        # Missing channel_title, category_id, views
    })
    is_valid, missing, present, msg = validate_schema(df)
    assert is_valid is False
    assert "channel_title" in missing
    assert "category_id" in missing
    assert "views" in missing
    assert "Schema validation failed" in msg


def test_load_csv_data_from_buffer():
    csv_content = """video_id,trending_date,title,channel_title,category_id,publish_time,tags,views,likes,dislikes,comment_count
abc1,17.14.11,"Title with, comma and हिन्दी",TestChannel,10,2017-11-13T17:00:00.000Z,tag1|tag2,50000,2000,50,300
"""
    buffer = io.BytesIO(csv_content.encode("utf-8"))
    df, meta = load_csv_data(buffer)
    assert len(df) == 1
    assert df.iloc[0]["video_id"] == "abc1"
    assert "हिन्दी" in df.iloc[0]["title"]
    assert meta["raw_row_count"] == 1
    assert meta["encoding"] in ["utf-8", "utf-8-sig"]


def test_load_category_mappings_fallback():
    # Calling with nonexistent file should fallback to STANDARD_CATEGORY_MAP
    mapping, is_custom = load_category_mappings("nonexistent_file_path.json")
    assert is_custom is False
    assert 10 in mapping
    assert mapping[10] == "Music"
    assert mapping[24] == "Entertainment"


def test_load_category_mappings_from_json_buffer():
    custom_json = {
        "items": [
            {"id": "100", "snippet": {"title": "Custom College Category"}},
            {"id": "101", "snippet": {"title": "BDA Project Tech"}},
        ]
    }
    buffer = io.StringIO(json.dumps(custom_json))
    mapping, is_custom = load_category_mappings(buffer)
    assert is_custom is True
    assert mapping[100] == "Custom College Category"
    assert mapping[101] == "BDA Project Tech"
