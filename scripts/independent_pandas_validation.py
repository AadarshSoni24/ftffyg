import json
import random
import urllib.request
import pandas as pd
from datetime import datetime, timedelta, timezone

def main():
    print("=" * 115)
    print("INDEPENDENT PANDAS RE-IMPLEMENTATION & 40-SAMPLE AUDIT (NO ENGINE IMPORT)")
    print("=" * 115)
    
    # 1. Load raw CSVs directly using pandas
    df_act = pd.read_csv("backend/data/actuals.csv")
    df_fc = pd.read_csv("backend/data/forecasts.csv")
    
    df_act["target_dt"] = pd.to_datetime(df_act["startTime"], utc=True)
    df_fc["target_dt"] = pd.to_datetime(df_fc["startTime"], utc=True)
    df_fc["pub_dt"] = pd.to_datetime(df_fc["publishTime"], utc=True)
    
    # Filter scope: 2 Jan 2026 to 1 Feb 2026
    start_dt = pd.to_datetime("2026-01-02T00:00:00Z", utc=True)
    end_dt = pd.to_datetime("2026-02-01T23:59:59Z", utc=True)
    
    scope_acts = df_act[(df_act["target_dt"] >= start_dt) & (df_act["target_dt"] <= end_dt)].sort_values("target_dt").reset_index(drop=True)
    
    # 2. Independent Day-Ahead selection logic in pandas:
    # For each delivery date D, cutoff is D-1 at 09:00 UTC
    pandas_aligned = {}
    
    # Group actuals by target date
    for _, act_row in scope_acts.iterrows():
        st_str = act_row["startTime"]
        target_dt = act_row["target_dt"]
        act_gen = act_row["generation"]
        period = act_row["settlementPeriod"]
        
        # Delivery date D
        delivery_date = target_dt.date()
        d_minus_1 = delivery_date - timedelta(days=1)
        cutoff_dt = pd.to_datetime(datetime(d_minus_1.year, d_minus_1.month, d_minus_1.day, 9, 0, 0, tzinfo=timezone.utc))
        
        # In WINDFOR, forecasts are hourly. Match target hour:
        hour_target_dt = target_dt.replace(minute=0, second=0)
        
        # Eligible forecasts for this target hour published <= cutoff_dt
        candidates = df_fc[(df_fc["target_dt"] == hour_target_dt) & (df_fc["pub_dt"] <= cutoff_dt)]
        
        if len(candidates) > 0:
            best_fc = candidates.sort_values("pub_dt").iloc[-1]
            fc_gen = float(best_fc["generation"])
            pub_str = str(best_fc["publishTime"])
        else:
            fc_gen = None
            pub_str = None
            
        err = round(fc_gen - act_gen, 2) if (fc_gen is not None and act_gen is not None) else None
        
        pandas_aligned[st_str] = {
            "startTime": st_str,
            "period": period,
            "actual": act_gen,
            "forecast": fc_gen,
            "publishTime": pub_str,
            "error": err,
        }
        
    print(f"Total periods evaluated independently by Pandas: {len(pandas_aligned)} (Expected: 1,488)")
    
    # 3. Fetch Engine results from live backend or local calculation
    url = "http://127.0.0.1:8000/api/dashboard?from=2026-01-02&to=2026-02-01&focus=2026-01-14&mode=dayahead&cutoff=9"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        dashboard_data = json.loads(resp.read().decode("utf-8"))
        
    engine_rows = {r["startTime"]: r for r in dashboard_data["rows"]}
    print(f"Total periods returned by FastAPI Engine: {len(engine_rows)} (Expected: 1,488)")
    
    # 4. Select exactly 40 specific half-hours:
    # Must include Jan 2 (start), Jan 3, Jan 4, Jan 5, Jan 6, Feb 1 (end), and 10 random other dates across Jan
    mandatory_targets = []
    
    # Jan 2 (5 periods)
    mandatory_targets += ["2026-01-02T00:00:00Z", "2026-01-02T05:30:00Z", "2026-01-02T11:30:00Z", "2026-01-02T17:30:00Z", "2026-01-02T23:30:00Z"]
    # Jan 3 (5 periods)
    mandatory_targets += ["2026-01-03T00:00:00Z", "2026-01-03T04:30:00Z", "2026-01-03T09:30:00Z", "2026-01-03T14:30:00Z", "2026-01-03T23:30:00Z"]
    # Jan 4 (5 periods)
    mandatory_targets += ["2026-01-04T00:00:00Z", "2026-01-04T06:00:00Z", "2026-01-04T12:00:00Z", "2026-01-04T18:00:00Z", "2026-01-04T23:30:00Z"]
    # Jan 5 (5 periods)
    mandatory_targets += ["2026-01-05T00:00:00Z", "2026-01-05T07:30:00Z", "2026-01-05T12:30:00Z", "2026-01-05T16:00:00Z", "2026-01-05T23:30:00Z"]
    # Jan 6 (5 periods)
    mandatory_targets += ["2026-01-06T00:00:00Z", "2026-01-06T08:00:00Z", "2026-01-06T13:30:00Z", "2026-01-06T19:00:00Z", "2026-01-06T23:30:00Z"]
    # Feb 1 (5 periods)
    mandatory_targets += ["2026-02-01T00:00:00Z", "2026-02-01T06:00:00Z", "2026-02-01T12:00:00Z", "2026-02-01T18:00:00Z", "2026-02-01T23:30:00Z"]
    
    # 10 key sample dates across the remainder of January
    additional_sample_dates = [
        "2026-01-08T12:00:00Z", # Jan 8 low wind
        "2026-01-10T15:30:00Z", # Jan 10 under-forecast day
        "2026-01-11T06:00:00Z", # Jan 11 ramp up
        "2026-01-12T18:00:00Z", # Jan 12 top over-forecast day
        "2026-01-14T17:30:00Z", # Jan 14 focus day peak
        "2026-01-19T08:00:00Z", # Jan 19 negative bias day
        "2026-01-21T21:00:00Z", # Jan 21 high wind
        "2026-01-24T18:00:00Z", # Jan 24 month-maximum actual (17,805 MW)
        "2026-01-27T14:00:00Z", # Jan 27 high forecast day
        "2026-01-28T09:30:00Z", # Jan 28 largest daily over-forecast (+5,375 MW)
    ]
    
    sample_targets = mandatory_targets + additional_sample_dates
    assert len(sample_targets) == 40, f"Expected 40 targets, got {len(sample_targets)}"
    
    print("\n" + "=" * 115)
    print(f"{'#':<3} | {'Delivery startTime':<21} | {'SP':>2} | {'Actual (MW)':>11} | {'Pd Fc (MW)':>10} | {'Eng Fc (MW)':>11} | {'Pd PubTime':<20} | {'Match':>5}")
    print("=" * 115)
    
    matches_count = 0
    for idx, st in enumerate(sample_targets, 1):
        p = pandas_aligned[st]
        e = engine_rows[st]
        
        act_match = p["actual"] == e["actual"]
        fc_match = p["forecast"] == e["forecast"]
        pub_match = p["publishTime"] == e["publishTime"]
        
        is_match = act_match and fc_match and pub_match
        if is_match:
            matches_count += 1
            match_str = "YES"
        else:
            match_str = "NO"
            
        print(f"{idx:<3} | {st:<21} | {p['period']:>2} | {p['actual']:>11.1f} | {p['forecast']:>10.1f} | {e['forecast']:>11.1f} | {p['publishTime']:<20} | {match_str:>5}")
        
    print("=" * 115)
    print(f"AUDIT SUMMARY: {matches_count} / 40 PERFECT MATCHES ({matches_count / 40 * 100:.1f}%)")
    print("=" * 115)

if __name__ == "__main__":
    main()
