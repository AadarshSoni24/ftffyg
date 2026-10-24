"""
backend/forecast_engine.py
Pure-function calculation engine for UK Wind Forecast analysis.
Scope: Delivery days whose D-1 purchase decision falls in January 2026 (2 Jan 2026 - 1 Feb 2026).

Handles:
  1. Day-ahead forecast selection (latest forecast available at D-1 cutoff time).
  2. Fixed horizon forecast selection (latest forecast published <= startTime - N hours).
  3. Half-hourly vs hourly alignment between FUELHH actuals and WINDFOR forecasts.
  4. Accuracy metrics calculation: MAE, RMSE, MAPE (zero-safe), bias, percentiles (P50, P90, P99).
  5. By-horizon metrics calculation (0 to 48 hours) and vintage effective-age scoring.
  6. Daily breakdown with exact mathematical reconciliation.
  7. Focus day metrics and 500 MW histogram binning with overflow bars.
"""

from datetime import datetime, timedelta, timezone
import math
from typing import List, Dict, Any, Optional, Tuple

DEFAULT_DELIVERY_START = "2026-01-02"
DEFAULT_DELIVERY_END = "2026-02-01"
DEFAULT_FOCUS_DAY = "2026-01-14"
DEFAULT_CUTOFF_HOUR = 9
DEFAULT_HORIZON_HOURS = 24.0


def ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_iso(dt_str: str) -> datetime:
    """Parse ISO8601 string to a timezone-aware UTC datetime object."""
    cleaned = dt_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_iso(dt: datetime) -> str:
    """Format datetime as UTC ISO8601 string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def to_epoch_ms(dt_str: str) -> int:
    """Convert ISO8601 string to millisecond timestamp (epoch) in explicit UTC."""
    dt = parse_iso(dt_str)
    return int(dt.timestamp() * 1000)


def filter_records_by_time_range(
    records: List[Dict[str, Any]],
    start_dt: datetime,
    end_dt: datetime,
    key: str = "startTime",
) -> List[Dict[str, Any]]:
    """Filter records where record[key] falls within [start_dt, end_dt] in UTC."""
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=timezone.utc)
        
    filtered = []
    for r in records:
        ts = parse_iso(r[key])
        if start_dt <= ts <= end_dt:
            filtered.append(r)
    return filtered


def get_latest_forecast_for_target(
    forecasts_for_target: List[Dict[str, Any]],
    cutoff_dt: datetime,
) -> Optional[Dict[str, Any]]:
    """
    Given all forecast records published for a specific target startTime,
    returns the latest forecast record whose publishTime <= cutoff_dt.
    Returns None if no forecast was published on or before cutoff_dt.
    """
    if cutoff_dt.tzinfo is None:
        cutoff_dt = cutoff_dt.replace(tzinfo=timezone.utc)
        
    eligible = [
        f for f in forecasts_for_target
        if parse_iso(f["publishTime"]) <= cutoff_dt
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda f: parse_iso(f["publishTime"]))


def build_day_ahead_forecasts(
    forecasts: List[Dict[str, Any]],
    target_start_dt: datetime,
    target_end_dt: datetime,
    cutoff_hour: int = 9,
    cutoff_minute: int = 0,
    expand_to_half_hours: bool = False,
) -> List[Dict[str, Any]]:
    """
    Day-ahead forecast logic:
    For each target delivery day D and target startTime,
    find the latest forecast published on or before Day D-1 at cutoff_hour:cutoff_minute UTC.
    Assumption: Default decision cutoff is 09:00 UTC on D-1.
    """
    if target_start_dt.tzinfo is None:
        target_start_dt = target_start_dt.replace(tzinfo=timezone.utc)
    if target_end_dt.tzinfo is None:
        target_end_dt = target_end_dt.replace(tzinfo=timezone.utc)

    by_target: Dict[str, List[Dict[str, Any]]] = {}
    for f in forecasts:
        st = f["startTime"]
        by_target.setdefault(st, []).append(f)

    results = []
    target_times = sorted([
        st for st in by_target.keys()
        if target_start_dt <= parse_iso(st) <= target_end_dt
    ])

    for st in target_times:
        target_dt = parse_iso(st)
        d_minus_1 = target_dt.date() - timedelta(days=1)
        cutoff_dt = datetime(
            d_minus_1.year, d_minus_1.month, d_minus_1.day,
            cutoff_hour, cutoff_minute, 0, tzinfo=timezone.utc
        )

        chosen = get_latest_forecast_for_target(by_target[st], cutoff_dt)
        if chosen:
            lead_h = round((target_dt - parse_iso(chosen["publishTime"])).total_seconds() / 3600.0, 1)
            results.append({
                "startTime": st,
                "publishTime": chosen["publishTime"],
                "generation": chosen["generation"],
                "cutoffTime": format_iso(cutoff_dt),
                "horizonHours": lead_h,
            })
            if expand_to_half_hours:
                dt_30 = target_dt + timedelta(minutes=30)
                if dt_30 <= target_end_dt:
                    lead_h_30 = round((dt_30 - parse_iso(chosen["publishTime"])).total_seconds() / 3600.0, 1)
                    results.append({
                        "startTime": format_iso(dt_30),
                        "publishTime": chosen["publishTime"],
                        "generation": chosen["generation"],
                        "cutoffTime": format_iso(cutoff_dt),
                        "horizonHours": lead_h_30,
                    })
        else:
            results.append({
                "startTime": st,
                "publishTime": None,
                "generation": None,
                "cutoffTime": format_iso(cutoff_dt),
                "horizonHours": None,
            })
            if expand_to_half_hours:
                dt_30 = target_dt + timedelta(minutes=30)
                if dt_30 <= target_end_dt:
                    results.append({
                        "startTime": format_iso(dt_30),
                        "publishTime": None,
                        "generation": None,
                        "cutoffTime": format_iso(cutoff_dt),
                        "horizonHours": None,
                    })

    return results


def build_horizon_forecasts(
    forecasts: List[Dict[str, Any]],
    target_start_dt: datetime,
    target_end_dt: datetime,
    horizon_hours: float = 24.0,
    expand_to_half_hours: bool = False,
) -> List[Dict[str, Any]]:
    """
    Fixed-horizon forecast logic:
    For each target startTime, return the latest forecast published <= startTime - horizon_hours.
    """
    if target_start_dt.tzinfo is None:
        target_start_dt = target_start_dt.replace(tzinfo=timezone.utc)
    if target_end_dt.tzinfo is None:
        target_end_dt = target_end_dt.replace(tzinfo=timezone.utc)

    by_target: Dict[str, List[Dict[str, Any]]] = {}
    for f in forecasts:
        st = f["startTime"]
        by_target.setdefault(st, []).append(f)

    results = []
    target_times = sorted([
        st for st in by_target.keys()
        if target_start_dt <= parse_iso(st) <= target_end_dt
    ])

    for st in target_times:
        target_dt = parse_iso(st)
        cutoff_dt = target_dt - timedelta(hours=horizon_hours)

        chosen = get_latest_forecast_for_target(by_target[st], cutoff_dt)
        if chosen:
            lead_h = round((target_dt - parse_iso(chosen["publishTime"])).total_seconds() / 3600.0, 1)
            results.append({
                "startTime": st,
                "publishTime": chosen["publishTime"],
                "generation": chosen["generation"],
                "cutoffTime": format_iso(cutoff_dt),
                "horizonHours": lead_h,
            })
            if expand_to_half_hours:
                dt_30 = target_dt + timedelta(minutes=30)
                if dt_30 <= target_end_dt:
                    lead_h_30 = round((dt_30 - parse_iso(chosen["publishTime"])).total_seconds() / 3600.0, 1)
                    results.append({
                        "startTime": format_iso(dt_30),
                        "publishTime": chosen["publishTime"],
                        "generation": chosen["generation"],
                        "cutoffTime": format_iso(cutoff_dt),
                        "horizonHours": lead_h_30,
                    })
        else:
            results.append({
                "startTime": st,
                "publishTime": None,
                "generation": None,
                "cutoffTime": format_iso(cutoff_dt),
                "horizonHours": None,
            })
            if expand_to_half_hours:
                dt_30 = target_dt + timedelta(minutes=30)
                if dt_30 <= target_end_dt:
                    results.append({
                        "startTime": format_iso(dt_30),
                        "publishTime": None,
                        "generation": None,
                        "cutoffTime": format_iso(cutoff_dt),
                        "horizonHours": None,
                    })

    return results


def align_actuals_with_forecasts(
    actuals: List[Dict[str, Any]],
    forecasts_list: List[Dict[str, Any]],
    expand_to_half_hours: bool = True,
) -> List[Dict[str, Any]]:
    """
    Aligns actual generation with forecast generation by target startTime.
    Includes epoch millisecond timestamp `t`, `publish` timestamp in ms,
    and effective `age` in hours for frontend rendering.
    """
    fc_by_time = {f["startTime"]: f for f in forecasts_list}
    act_by_time = {a["startTime"]: a for a in actuals}

    aligned = []
    for act_time_str in sorted(act_by_time.keys()):
        act = act_by_time[act_time_str]
        act_dt = parse_iso(act_time_str)
        t_ms = to_epoch_ms(act_time_str)
        
        fc = None
        if act_time_str in fc_by_time:
            fc = fc_by_time[act_time_str]
        elif expand_to_half_hours and act_dt.minute == 30:
            hour_start_str = format_iso(act_dt.replace(minute=0, second=0))
            fc = fc_by_time.get(hour_start_str)

        if fc is not None:
            actual_gen = act.get("generation")
            fc_gen = fc.get("generation")
            pub_str = fc.get("publishTime")
            pub_ms = to_epoch_ms(pub_str) if pub_str else None
            
            error = None
            abs_error = None
            age_h = None
            if actual_gen is not None and fc_gen is not None:
                error = round(fc_gen - actual_gen, 2)
                abs_error = round(abs(error), 2)
            if pub_str:
                age_h = round((act_dt - parse_iso(pub_str)).total_seconds() / 3600.0, 2)

            aligned.append({
                "t": t_ms,
                "startTime": act_time_str,
                "settlementDate": act.get("settlementDate"),
                "settlementPeriod": act.get("settlementPeriod"),
                "actual": actual_gen,
                "forecast": fc_gen,
                "publish": pub_ms,
                "publishTime": pub_str,
                "error": error,
                "absoluteError": abs_error,
                "age": age_h,
            })
        elif not expand_to_half_hours and act_dt.minute != 0:
            continue
        else:
            aligned.append({
                "t": t_ms,
                "startTime": act_time_str,
                "settlementDate": act.get("settlementDate"),
                "settlementPeriod": act.get("settlementPeriod"),
                "actual": act.get("generation"),
                "forecast": None,
                "publish": None,
                "publishTime": None,
                "error": None,
                "absoluteError": None,
                "age": None,
            })

    return aligned


def compute_metrics(aligned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes summary accuracy metrics:
      - MAE, RMSE, Bias, MAPE (zero-safe), Percentiles (P50, P90, P99)
      - Coverage counts
      - 500 MW histogram bins with overflow bars
      - Descriptive plain-English insight (no causes, no trading advice)
    """
    total_periods = len(aligned_data)
    valid_pairs = [
        d for d in aligned_data
        if d.get("actual") is not None and d.get("forecast") is not None
    ]
    matched_periods = len(valid_pairs)
    coverage_pct = round((matched_periods / max(total_periods, 1)) * 100.0, 1)

    no_forecast_count = sum(1 for d in aligned_data if d.get("forecast") is None)
    no_actual_count = sum(1 for d in aligned_data if d.get("actual") is None)

    if not valid_pairs:
        return {
            "totalPeriods": total_periods,
            "matchedPeriods": 0,
            "coveragePct": 0.0,
            "coverage": {
                "matched": 0,
                "total": total_periods,
                "noForecast": no_forecast_count,
                "noActual": no_actual_count,
            },
            "mae": None,
            "rmse": None,
            "bias": None,
            "mape": None,
            "p50": None,
            "p90": None,
            "p99": None,
            "insight": "No matching actuals and forecasts found for the selected criteria.",
            "histogram": {"bins": [], "limit": 5000, "width": 500},
            "ageSpan": None,
        }

    errors = [d["error"] for d in valid_pairs]
    abs_errors = [d["absoluteError"] for d in valid_pairs]
    n = len(valid_pairs)

    mae = round(sum(abs_errors) / n, 1)
    rmse = round(math.sqrt(sum(e * e for e in errors) / n), 1)
    bias = round(sum(errors) / n, 1)

    # Zero-safe MAPE on periods where actual > 50 MW
    mape_eligible = [
        abs(d["error"]) / d["actual"]
        for d in valid_pairs
        if d["actual"] is not None and d["actual"] > 50.0
    ]
    mape = round((sum(mape_eligible) / len(mape_eligible)) * 100.0, 2) if mape_eligible else None

    # Percentiles
    sorted_abs = sorted(abs_errors)
    def get_percentile(sorted_list: List[float], p: float) -> float:
        if not sorted_list:
            return 0.0
        idx = (len(sorted_list) - 1) * p
        lower = int(math.floor(idx))
        upper = int(math.ceil(idx))
        if lower == upper:
            return sorted_list[lower]
        weight = idx - lower
        return round(sorted_list[lower] * (1 - weight) + sorted_list[upper] * weight, 1)

    p50 = get_percentile(sorted_abs, 0.50)
    p90 = get_percentile(sorted_abs, 0.90)
    p99 = get_percentile(sorted_abs, 0.99)

    # Descriptive takeaway banner (strictly factual, no causal claims, no purchase advice)
    direction = "too high" if bias >= 0 else "too low"
    insight = (
        f"On average the forecast was {abs(bias):,.0f} MW {direction} across this period. "
        f"In 9 out of 10 half-hours, the absolute forecast error stayed within {p90:,.0f} MW."
    )

    # 500 MW histogram bins with overflow bars
    histogram_bins = build_500mw_histogram(errors, limit=5000.0, width=500.0)

    # Age span
    valid_ages = [d["age"] for d in valid_pairs if d.get("age") is not None]
    age_span = [round(min(valid_ages), 1), round(max(valid_ages), 1)] if valid_ages else None

    hist_obj = {
        "bins": histogram_bins,
        "limit": 5000,
        "width": 500,
    }

    return {
        "totalPeriods": total_periods,
        "matchedPeriods": matched_periods,
        "coveragePct": coverage_pct,
        "coverage": {
            "matched": matched_periods,
            "total": total_periods,
            "noForecast": no_forecast_count,
            "noActual": no_actual_count,
        },
        "mae": mae,
        "rmse": rmse,
        "bias": bias,
        "mape": mape,
        "p50": p50,
        "p90": p90,
        "p99": p99,
        "insight": insight,
        "histogram": hist_obj,
        "errorDistribution": histogram_bins,
        "ageSpan": age_span,
    }


def build_500mw_histogram(errors: List[float], limit: float = 5000.0, width: float = 500.0) -> List[Dict[str, Any]]:
    """
    Constructs fixed 500 MW histogram bins from -limit to +limit.
    Outer bins collect all errors <= -limit and >= +limit (overflow bars).
    Matching the exact shape expected by ErrorHistogram.jsx: { x0, x1, mid, count }.
    """
    num_bins = int((2 * limit) / width)  # 20 bins
    bins = []
    for i in range(num_bins):
        x0 = -limit + i * width
        x1 = x0 + width
        mid = x0 + width / 2.0
        bins.append({
            "x0": round(x0, 0),
            "x1": round(x1, 0),
            "mid": round(mid, 0),
            "count": 0,
        })

    for e in errors:
        if e <= -limit:
            bins[0]["count"] += 1
        elif e >= limit:
            bins[-1]["count"] += 1
        else:
            idx = int(math.floor((e + limit) / width))
            idx = min(num_bins - 1, max(0, idx))
            bins[idx]["count"] += 1

    return bins


def compute_daily_breakdown(aligned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Groups aligned half-hourly data by delivery day and computes daily statistics.
    Provides mathematical reconciliation checks between daily figures and monthly totals:
      - Sum of daily signed errors == overall total signed error
      - Weighted mean of daily biases == overall bias
      - Weighted mean of daily MAEs == overall MAE
      - Mean daily forecast - Mean daily actual == overall bias
    """
    by_day: Dict[str, List[Dict[str, Any]]] = {}
    for r in aligned_data:
        d = r["startTime"][:10]
        by_day.setdefault(d, []).append(r)

    total_signed_error = sum(r["error"] for r in aligned_data if r.get("error") is not None)
    total_abs_error = sum(r["absoluteError"] for r in aligned_data if r.get("error") is not None)
    total_matched = sum(1 for r in aligned_data if r.get("error") is not None)

    overall_bias = round(total_signed_error / max(total_matched, 1), 1)
    overall_mae = round(total_abs_error / max(total_matched, 1), 1)

    daily_rows = []
    for day_str in sorted(by_day.keys()):
        rows = by_day[day_str]
        acts = [r["actual"] for r in rows if r.get("actual") is not None]
        fcs = [r["forecast"] for r in rows if r.get("forecast") is not None]
        errs = [r["error"] for r in rows if r.get("error") is not None]
        abs_errs = [r["absoluteError"] for r in rows if r.get("error") is not None]

        n = len(errs)
        avg_act = round(sum(acts) / len(acts), 1) if acts else 0.0
        max_act = round(max(acts), 1) if acts else 0.0
        min_act = round(min(acts), 1) if acts else 0.0

        avg_fc = round(sum(fcs) / len(fcs), 1) if fcs else 0.0
        max_fc = round(max(fcs), 1) if fcs else 0.0
        min_fc = round(min(fcs), 1) if fcs else 0.0

        signed_err_sum = sum(errs) if errs else 0.0
        abs_err_sum = sum(abs_errs) if abs_errs else 0.0

        # Exact mathematical reconciliation: day_bias matches avgForecast - avgActual
        day_bias = round(avg_fc - avg_act, 1)
        day_mae = round(abs_err_sum / max(n, 1), 1)
        day_rmse = round(math.sqrt(sum(e * e for e in errs) / max(n, 1)), 1) if errs else 0.0

        bias_share = round((signed_err_sum / max(total_signed_error, 1e-9)) * 100.0, 2)

        daily_rows.append({
            "date": day_str,
            "periods": len(rows),
            "matched": n,
            "avgActual": avg_act,
            "minActual": min_act,
            "maxActual": max_act,
            "avgForecast": avg_fc,
            "minForecast": min_fc,
            "maxForecast": max_fc,
            "bias": day_bias,
            "mae": day_mae,
            "rmse": day_rmse,
            "signedErrorSum": round(signed_err_sum, 1),
            "absErrorSum": round(abs_err_sum, 1),
            "shareOfMonthlyBias": bias_share,
        })

    # Mathematical reconciliation verification
    sum_signed_error = sum(d["signedErrorSum"] for d in daily_rows)
    weighted_mean_bias = round(sum(d["signedErrorSum"] for d in daily_rows) / max(total_matched, 1), 1)
    weighted_mean_mae = round(sum(d["absErrorSum"] for d in daily_rows) / max(total_matched, 1), 1)

    diff_bias = round(abs(overall_bias - weighted_mean_bias), 4)
    diff_mae = round(abs(overall_mae - weighted_mean_mae), 4)

    return {
        "daily": daily_rows,
        "reconciliation": {
            "totalDays": len(daily_rows),
            "totalPeriods": len(aligned_data),
            "totalMatched": total_matched,
            "totalSignedError": round(total_signed_error, 1),
            "totalAbsError": round(total_abs_error, 1),
            "overallBias": overall_bias,
            "overallMae": overall_mae,
            "weightedDailyBias": weighted_mean_bias,
            "weightedDailyMae": weighted_mean_mae,
            "reconciliationDiffBias": diff_bias,
            "reconciliationDiffMae": diff_mae,
            "reconciliationStatus": "PASSED" if (diff_bias < 0.1 and diff_mae < 0.1) else "FAILED",
        },
    }


def compute_focus_day_details(
    focus_date_str: str,
    aligned_data: List[Dict[str, Any]],
    all_forecasts: List[Dict[str, Any]],
    cutoff_hour: int = 9,
) -> Dict[str, Any]:
    """
    Computes all focus day fields required by Hero.jsx:
      - avgForecast, avgActual
      - peak half-hour ({ t, iso, forecast })
      - publishTimes list and latest 'asOf' publishTime
      - effective horizon ages [minAge, maxAge]
      - day stats (MAE, RMSE, Bias, P90)
      - count of available forecasts
    """
    focus_rows = [r for r in aligned_data if r["startTime"].startswith(focus_date_str)]
    valid_fcs = [r for r in focus_rows if r.get("forecast") is not None]
    valid_acts = [r for r in focus_rows if r.get("actual") is not None]

    avg_fc = round(sum(r["forecast"] for r in valid_fcs) / len(valid_fcs), 1) if valid_fcs else None
    avg_act = round(sum(r["actual"] for r in valid_acts) / len(valid_acts), 1) if valid_acts else None

    # Peak half-hour forecast
    peak = None
    if valid_fcs:
        peak_row = max(valid_fcs, key=lambda r: r["forecast"])
        peak = {
            "t": peak_row["t"],
            "startTime": peak_row["startTime"],
            "forecast": peak_row["forecast"],
        }

    # Distinct publish times used for this day's forecasts
    pubs = sorted(list(set(r["publish"] for r in valid_fcs if r.get("publish") is not None)))
    pubs_iso = sorted(list(set(r["publishTime"] for r in valid_fcs if r.get("publishTime") is not None)))
    as_of = pubs_iso[-1] if pubs_iso else None
    as_of_ms = pubs[-1] if pubs else None

    # Ages
    ages = [r["age"] for r in valid_fcs if r.get("age") is not None]
    age_span = [round(min(ages), 1), round(max(ages), 1)] if ages else None

    # Day stats
    focus_metrics = compute_metrics(focus_rows)
    stats = {
        "n": focus_metrics["matchedPeriods"],
        "mae": focus_metrics["mae"],
        "rmse": focus_metrics["rmse"],
        "bias": focus_metrics["bias"],
        "p90": focus_metrics["p90"],
    } if focus_metrics["matchedPeriods"] > 0 else None

    return {
        "date": focus_date_str,
        "avgForecast": avg_fc,
        "avgActual": avg_act,
        "peak": peak,
        "peakHalfHour": peak,
        "publishTimes": pubs,
        "publishTimesIso": pubs_iso,
        "asOf": as_of,
        "asOfPublishTime": as_of,
        "asOfMs": as_of_ms,
        "ages": age_span,
        "effectiveHorizonRange": f"{age_span[0]}h - {age_span[1]}h" if age_span else None,
        "minHorizonHours": age_span[0] if age_span else None,
        "maxHorizonHours": age_span[1] if age_span else None,
        "stats": stats,
        "available": len(valid_fcs),
    }


def compute_vintage_effective_age_horizon(
    forecasts: List[Dict[str, Any]],
    actuals: List[Dict[str, Any]],
    target_start_dt: datetime,
    target_end_dt: datetime,
    max_age_hours: int = 48,
    bin_width: int = 2,
) -> List[Dict[str, Any]]:
    """
    Scores every published forecast vintage for in-range targets independently
    at its own effective age (target_time - publishTime).
    Creates 24 two-hour bins: [0-2h], [2-4h], ..., [46-48h].
    Matching the exact shape expected by HorizonChart.jsx: { mid, from, to, sum, n, mae }.
    """
    act_map = {a["startTime"]: a["generation"] for a in actuals if a.get("generation") is not None}
    
    target_start_dt = ensure_utc(target_start_dt)
    target_end_dt = ensure_utc(target_end_dt)

    num_bins = int(max_age_hours / bin_width)
    bins = [
        {"mid": i * bin_width + (bin_width / 2.0), "from": i * bin_width, "to": (i + 1) * bin_width, "sum": 0.0, "n": 0}
        for i in range(num_bins)
    ]

    for f in forecasts:
        st_str = f.get("startTime")
        pub_str = f.get("publishTime")
        fc_gen = f.get("generation")
        if not st_str or not pub_str or fc_gen is None:
            continue

        target_dt = parse_iso(st_str)
        if not (target_start_dt <= target_dt <= target_end_dt):
            continue

        pub_dt = parse_iso(pub_str)
        age = (target_dt - pub_dt).total_seconds() / 3600.0

        # Only evaluate non-negative horizons up to max_age_hours
        if age < 0 or age > max_age_hours:
            continue

        # Half-hour alignment: test both :00 and :30
        for minute_offset in [0, 30]:
            lookup_dt = target_dt + timedelta(minutes=minute_offset)
            lookup_str = format_iso(lookup_dt)
            if lookup_str in act_map:
                act_gen = act_map[lookup_str]
                err = abs(fc_gen - act_gen)
                
                bin_idx = int(math.floor(age / bin_width))
                bin_idx = min(num_bins - 1, max(0, bin_idx))
                bins[bin_idx]["sum"] += err
                bins[bin_idx]["n"] += 1

    return [
        {
            "mid": b["mid"],
            "from": b["from"],
            "to": b["to"],
            "sum": round(b["sum"], 1),
            "n": b["n"],
            "mae": round(b["sum"] / b["n"], 1) if b["n"] > 0 else None,
        }
        for b in bins
    ]


def compute_metrics_by_horizon(
    actuals: List[Dict[str, Any]],
    forecasts: List[Dict[str, Any]],
    target_start_dt: datetime,
    target_end_dt: datetime,
    horizons: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Computes accuracy metrics (MAE, RMSE, bias, P90) across specified horizons.
    """
    if horizons is None:
        horizons = list(range(0, 49, 3))

    results = []
    for h in horizons:
        fc_list = build_horizon_forecasts(
            forecasts,
            target_start_dt,
            target_end_dt,
            horizon_hours=float(h),
        )
        aligned = align_actuals_with_forecasts(actuals, fc_list, expand_to_half_hours=True)
        m = compute_metrics(aligned)
        results.append({
            "horizonHours": h,
            "mae": m["mae"],
            "rmse": m["rmse"],
            "bias": m["bias"],
            "p90": m["p90"],
            "matchedPeriods": m["matchedPeriods"],
            "coveragePct": m["coveragePct"],
        })
    return results
