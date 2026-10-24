"""
scripts/fetch_data.py
Fetches UK National Wind actuals (FUELHH) and forecasts (WINDFOR) from Elexon BMRS API.
Saves cleaned datasets locally to backend/data/ so the application never calls Elexon at runtime.
Scope: Deliveries in January 2026, with margin from 2025-12-20 to 2026-02-06.
"""

import os
import sys
import json
import csv
import time
from datetime import datetime, timedelta
import requests

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data")

START_DATE = datetime(2025, 12, 20)
END_DATE = datetime(2026, 2, 6)


def fetch_actuals_fuelhh(start_dt: datetime, end_dt: datetime) -> list:
    """
    Fetch actual half-hourly generation from FUELHH dataset, filtering for fuelType='WIND'.
    Uses settlementDateFrom and settlementDateTo chunked by 7 days.
    """
    print(f"[1/2] Fetching actual wind generation (FUELHH) from {start_dt.date()} to {end_dt.date()}...")
    actuals = []
    curr = start_dt

    while curr < end_dt:
        chunk_end = min(curr + timedelta(days=7), end_dt)
        url = (
            f"{ELEXON_BASE_URL}/datasets/FUELHH/stream"
            f"?settlementDateFrom={curr.strftime('%Y-%m-%d')}"
            f"&settlementDateTo={chunk_end.strftime('%Y-%m-%d')}"
        )
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                # Filter strictly for WIND
                wind_records = [
                    {
                        "startTime": r["startTime"],
                        "settlementDate": r.get("settlementDate", ""),
                        "settlementPeriod": r.get("settlementPeriod", 0),
                        "generation": float(r["generation"]) if r.get("generation") is not None else None,
                    }
                    for r in data
                    if r.get("fuelType") == "WIND" and r.get("startTime")
                ]
                actuals.extend(wind_records)
                print(f"  Chunk {curr.date()} to {chunk_end.date()}: {len(wind_records)} WIND records")
                break
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed for {curr.date()}: {e}")
                time.sleep(2)
        curr = chunk_end + timedelta(days=1)

    # Deduplicate by startTime
    deduped = {}
    for r in actuals:
        deduped[r["startTime"]] = r
    sorted_actuals = [deduped[k] for k in sorted(deduped.keys())]
    return sorted_actuals


def fetch_forecasts_windfor(start_dt: datetime, end_dt: datetime) -> list:
    """
    Fetch wind forecasts from WINDFOR dataset.
    Uses publishDateTimeFrom and publishDateTimeTo chunked by 7 days.
    """
    print(f"[2/2] Fetching wind forecasts (WINDFOR) from {start_dt.date()} to {end_dt.date()}...")
    forecasts = []
    curr = start_dt

    while curr < end_dt:
        chunk_end = min(curr + timedelta(days=7), end_dt)
        url = (
            f"{ELEXON_BASE_URL}/datasets/WINDFOR/stream"
            f"?publishDateTimeFrom={curr.isoformat()}Z"
            f"&publishDateTimeTo={chunk_end.isoformat()}Z"
        )
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                records = [
                    {
                        "startTime": r["startTime"],
                        "publishTime": r["publishTime"],
                        "generation": float(r["generation"]) if r.get("generation") is not None else None,
                    }
                    for r in data
                    if r.get("startTime") and r.get("publishTime")
                ]
                forecasts.extend(records)
                print(f"  Chunk {curr.date()} to {chunk_end.date()}: {len(records)} forecast records")
                break
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed for {curr.date()}: {e}")
                time.sleep(2)
        curr = chunk_end

    # Deduplicate by (publishTime, startTime)
    deduped = {}
    for r in forecasts:
        deduped[(r["publishTime"], r["startTime"])] = r
    sorted_forecasts = [deduped[k] for k in sorted(deduped.keys())]
    return sorted_forecasts


def print_stats_and_save(actuals: list, forecasts: list):
    """
    Compute validation metrics, print stats, and write clean CSV and JSON files.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Actuals Stats
    act_nulls = sum(1 for a in actuals if a["generation"] is None)
    act_gens = [a["generation"] for a in actuals if a["generation"] is not None]
    act_start = actuals[0]["startTime"] if actuals else "N/A"
    act_end = actuals[-1]["startTime"] if actuals else "N/A"

    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT: ACTUALS (FUELHH, fuelType=WIND)")
    print("=" * 60)
    print(f"Total Rows:        {len(actuals)}")
    print(f"Start Time Range:  {act_start} -> {act_end}")
    print(f"Missing/Null Gen:  {act_nulls} ({(act_nulls / max(len(actuals), 1)) * 100:.2f}%)")
    if act_gens:
        print(f"Min Generation:    {min(act_gens):.1f} MW")
        print(f"Max Generation:    {max(act_gens):.1f} MW")
        print(f"Mean Generation:   {sum(act_gens)/len(act_gens):.1f} MW")

    # Forecasts Stats
    fc_nulls = sum(1 for f in forecasts if f["generation"] is None)
    fc_gens = [f["generation"] for f in forecasts if f["generation"] is not None]
    fc_pub_times = sorted(set(f["publishTime"] for f in forecasts))
    fc_start_times = sorted(set(f["startTime"] for f in forecasts))

    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT: FORECASTS (WINDFOR)")
    print("=" * 60)
    print(f"Total Rows:        {len(forecasts)}")
    print(f"Publish Time Range:{fc_pub_times[0] if fc_pub_times else 'N/A'} -> {fc_pub_times[-1] if fc_pub_times else 'N/A'}")
    print(f"Unique PublishTs:  {len(fc_pub_times)}")
    print(f"Target Start Range:{fc_start_times[0] if fc_start_times else 'N/A'} -> {fc_start_times[-1] if fc_start_times else 'N/A'}")
    print(f"Unique TargetTs:   {len(fc_start_times)}")
    print(f"Missing/Null Gen:  {fc_nulls} ({(fc_nulls / max(len(forecasts), 1)) * 100:.2f}%)")
    if fc_gens:
        print(f"Min Generation:    {min(fc_gens):.1f} MW")
        print(f"Max Generation:    {max(fc_gens):.1f} MW")
        print(f"Mean Generation:   {sum(fc_gens)/len(fc_gens):.1f} MW")

    # Check Jan 2026 coverage specifically
    jan_actuals = [a for a in actuals if a["startTime"].startswith("2026-01")]
    jan_fc_targets = [f for f in forecasts if f["startTime"].startswith("2026-01")]
    print("\n" + "=" * 60)
    print("JANUARY 2026 DELIVERY SPECIFIC COVERAGE")
    print("=" * 60)
    print(f"Jan 2026 Actuals Count:    {len(jan_actuals)} half-hours (Expected: 31 * 48 = 1488)")
    print(f"Jan 2026 Forecast Rows:    {len(jan_fc_targets)} target forecasts")
    unique_jan_targets = len(set(f["startTime"] for f in jan_fc_targets))
    print(f"Jan 2026 Target Hours:     {unique_jan_targets} hourly targets (Expected: 31 * 24 = 744)")
    print("=" * 60 + "\n")

    # Save Actuals CSV
    act_csv_path = os.path.join(OUTPUT_DIR, "actuals.csv")
    with open(act_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["startTime", "settlementDate", "settlementPeriod", "generation"])
        writer.writeheader()
        writer.writerows(actuals)

    # Save Forecasts CSV
    fc_csv_path = os.path.join(OUTPUT_DIR, "forecasts.csv")
    with open(fc_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["startTime", "publishTime", "generation"])
        writer.writeheader()
        writer.writerows(forecasts)

    print(f"Saved actuals to:   {act_csv_path}")
    print(f"Saved forecasts to: {fc_csv_path}")


def main():
    actuals = fetch_actuals_fuelhh(START_DATE, END_DATE)
    forecasts = fetch_forecasts_windfor(START_DATE, END_DATE)
    print_stats_and_save(actuals, forecasts)


if __name__ == "__main__":
    main()
