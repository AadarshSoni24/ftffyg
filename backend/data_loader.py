"""
backend/data_loader.py
Loads pre-fetched Elexon datasets from backend/data/ into memory.
Caches records on startup for fast, sub-millisecond API responses.
"""

import os
import csv
import json
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

_CACHED_ACTUALS: Optional[List[Dict[str, Any]]] = None
_CACHED_FORECASTS: Optional[List[Dict[str, Any]]] = None


def get_actuals_file_path() -> str:
    """Returns the path to actuals CSV data."""
    return os.path.join(DATA_DIR, "actuals.csv")


def get_forecasts_file_path() -> str:
    """Returns the path to forecasts CSV data."""
    return os.path.join(DATA_DIR, "forecasts.csv")


def load_actuals() -> List[Dict[str, Any]]:
    """Loads actual wind generation from local CSV storage."""
    global _CACHED_ACTUALS
    if _CACHED_ACTUALS is not None:
        return _CACHED_ACTUALS

    file_path = get_actuals_file_path()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Actuals data file not found at {file_path}. Run scripts/fetch_data.py first.")

    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            records.append({
                "startTime": r["startTime"],
                "settlementDate": r.get("settlementDate", ""),
                "settlementPeriod": int(r["settlementPeriod"]) if r.get("settlementPeriod") else 0,
                "generation": float(r["generation"]) if r.get("generation") else None,
            })

    _CACHED_ACTUALS = records
    return _CACHED_ACTUALS


def load_forecasts() -> List[Dict[str, Any]]:
    """Loads wind forecasts from local CSV storage."""
    global _CACHED_FORECASTS
    if _CACHED_FORECASTS is not None:
        return _CACHED_FORECASTS

    file_path = get_forecasts_file_path()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Forecasts data file not found at {file_path}. Run scripts/fetch_data.py first.")

    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            records.append({
                "startTime": r["startTime"],
                "publishTime": r["publishTime"],
                "generation": float(r["generation"]) if r.get("generation") else None,
            })

    _CACHED_FORECASTS = records
    return _CACHED_FORECASTS


def reload_data():
    """Forces cache invalidation and reload."""
    global _CACHED_ACTUALS, _CACHED_FORECASTS
    _CACHED_ACTUALS = None
    _CACHED_FORECASTS = None
    load_actuals()
    load_forecasts()
