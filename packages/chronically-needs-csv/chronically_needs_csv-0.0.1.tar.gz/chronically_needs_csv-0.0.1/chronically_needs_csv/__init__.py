"""
chronically-needs-csv

A JSON to CSV converter for people who chronically can't be bothered to learn json.load().
Dedicated to Konstantinos Chronis, who has mass amounts of time (Chronos) yet somehow
still needs someone else to convert his JSON files.

Usage:
    chronically-needs-csv data.json
    python -m chronically_needs_csv data.json
"""

import json
import csv
import io
from pathlib import Path
from typing import Any

__version__ = "0.0.1"  # Chronis Edition
__author__ = "A friend who got tired of converting JSON files"

# The messages that appear when Konstantinos runs this
CHRONIS_MESSAGES = [
    "Converting JSON to CSV... something an analyst could do themselves.",
    "Ah yes, another JSON file. Konstantinos strikes again.",
    "This one's for you, Chronis. You owe me a coffee.",
    "JSON → CSV complete. You're welcome, Konstantinos.",
    "Chronically converting files for Chronis since 2025.",
    "Fun fact: Python has json.load() built in. Just saying, Konstantinos.",
]


def _get_chronis_message() -> str:
    """Get a random message for our favorite analyst."""
    import random
    return random.choice(CHRONIS_MESSAGES)


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Flatten a nested dictionary using dot notation.

    Example:
        {"user": {"name": "John", "age": 30}}
        becomes
        {"user.name": "John", "user.age": 30}
    """
    items = []
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def normalize_value(value: Any, array_delimiter: str = ", ") -> str:
    """Convert a value to a CSV-friendly string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return array_delimiter.join(str(normalize_value(v, array_delimiter)) for v in value)
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def json_to_rows(data: Any) -> list[dict]:
    """
    Convert JSON data to a list of flat dictionaries (rows).
    Handles single objects, arrays of objects, and nested structures.
    """
    if isinstance(data, dict):
        records = [data]
    elif isinstance(data, list):
        if len(data) == 0:
            return []
        if not isinstance(data[0], dict):
            records = [{"value": item} for item in data]
        else:
            records = data
    else:
        records = [{"value": data}]

    return [flatten_dict(record) for record in records]


def json_to_csv_string(data: Any, array_delimiter: str = ", ") -> str:
    """
    Convert JSON data to a CSV string.

    Args:
        data: Parsed JSON data (dict, list, or primitive)
        array_delimiter: String to join array elements (default: ", ")

    Returns:
        CSV formatted string
    """
    rows = json_to_rows(data)
    if not rows:
        return ""

    all_keys = []
    seen_keys = set()
    for row in rows:
        for key in row.keys():
            if key not in seen_keys:
                all_keys.append(key)
                seen_keys.add(key)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys, extrasaction="ignore")
    writer.writeheader()

    for row in rows:
        normalized_row = {k: normalize_value(v, array_delimiter) for k, v in row.items()}
        writer.writerow(normalized_row)

    return output.getvalue()


def convert(
    input_path: str,
    output_path: str | None = None,
    array_delimiter: str = ", ",
    silent: bool = False
) -> str:
    """
    Convert a JSON file to CSV.

    Args:
        input_path: Path to input JSON file
        output_path: Path to output CSV file (default: input with .csv extension)
        array_delimiter: String to join array elements
        silent: If True, don't print the Chronis message

    Returns:
        Path to the output file
    """
    input_path = Path(input_path)

    if output_path is None:
        output_path = input_path.with_suffix(".csv")
    else:
        output_path = Path(output_path)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    csv_content = json_to_csv_string(data, array_delimiter)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(csv_content)

    return str(output_path)
