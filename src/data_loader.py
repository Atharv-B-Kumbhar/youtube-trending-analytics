"""
Data Loader Module for YouTube Trending Video Analytics.
Provides robust loading of CSV datasets (local or uploaded) and Category JSON mappings.
Handles encoding fallbacks, schema validation, and Unicode preservation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from config import (
    DEFAULT_CATEGORY_JSON,
    REQUIRED_COLUMNS,
    STANDARD_CATEGORY_MAP,
)


def load_category_mappings(
    json_source: Optional[Union[str, Path, Any]] = None
) -> Tuple[Dict[int, str], bool]:
    """
    Loads YouTube Category ID to Category Name mappings.
    Checks the specified file, the default path, and gracefully falls back
    to standard YouTube Category ID mappings if the file is missing or invalid.

    Returns:
        tuple: (category_map: dict[int, str], is_custom_file: bool)
    """
    target_path = None
    if json_source is not None:
        if isinstance(json_source, (str, Path)):
            target_path = Path(json_source)
        elif hasattr(json_source, "read"):
            # Uploaded file / buffer
            try:
                data = json.load(json_source)
                mapping = {}
                for item in data.get("items", []):
                    cat_id = int(item["id"])
                    cat_name = item.get("snippet", {}).get("title", f"Category {cat_id}")
                    mapping[cat_id] = cat_name
                return mapping, True
            except Exception:
                pass
    elif DEFAULT_CATEGORY_JSON.exists():
        target_path = DEFAULT_CATEGORY_JSON

    if target_path and target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mapping = {}
            for item in data.get("items", []):
                cat_id = int(item["id"])
                cat_name = item.get("snippet", {}).get("title", f"Category {cat_id}")
                mapping[cat_id] = cat_name
            if mapping:
                return mapping, True
        except Exception:
            pass

    # Graceful fallback to built-in standard YouTube categories
    return STANDARD_CATEGORY_MAP.copy(), False


def load_csv_data(
    file_source: Union[str, Path, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Loads the YouTube trending CSV dataset from a file path or uploaded file buffer.
    Attempts multiple encodings (utf-8, utf-8-sig, latin-1, cp1252) to handle
    international titles and regional characters without crashing.

    Returns:
        tuple: (DataFrame, metadata_dict)
    """
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    df = None
    used_encoding = None
    last_error = None

    for enc in encodings_to_try:
        try:
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            df = pd.read_csv(
                file_source,
                encoding=enc,
                low_memory=False,
                on_bad_lines="skip",
            )
            used_encoding = enc
            break
        except Exception as e:
            last_error = e
            continue

    if df is None:
        raise ValueError(
            f"Failed to read CSV with supported encodings ({', '.join(encodings_to_try)}). "
            f"Original error: {last_error}"
        )

    # Standardize column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]

    metadata = {
        "raw_row_count": len(df),
        "raw_column_count": len(df.columns),
        "columns": list(df.columns),
        "encoding": used_encoding,
    }

    return df, metadata


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str], List[str], str]:
    """
    Validates that the DataFrame has the mandatory columns needed for analytics.

    Returns:
        tuple: (is_valid: bool, missing_columns: list, present_columns: list, message: str)
    """
    present_cols = list(df.columns)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in present_cols]

    if missing_cols:
        msg = (
            f"Schema validation failed: Missing required column(s): {', '.join(missing_cols)}. "
            f"Required columns are: {', '.join(REQUIRED_COLUMNS)}."
        )
        return False, missing_cols, present_cols, msg

    return True, [], present_cols, "Schema validation successful. All required columns are present."
