"""
backend/main.py
FastAPI application serving UK Wind Actuals and Forecasts from Elexon BMRS.
Scope: Delivery days whose D-1 purchase decisions fall in January 2026 (2 Jan 2026 - 1 Feb 2026).
"""

from datetime import datetime, time, timezone
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .forecast_engine import (
    DEFAULT_DELIVERY_START,
    DEFAULT_DELIVERY_END,
    DEFAULT_FOCUS_DAY,
    DEFAULT_CUTOFF_HOUR,
    DEFAULT_HORIZON_HOURS,
    parse_iso,
    format_iso,
    filter_records_by_time_range,
    build_day_ahead_forecasts,
    build_horizon_forecasts,
    align_actuals_with_forecasts,
    compute_metrics,
    compute_metrics_by_horizon,
    compute_daily_breakdown,
    compute_focus_day_details,
    compute_vintage_effective_age_horizon,
)
from .data_loader import load_actuals, load_forecasts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm data cache on startup
    load_actuals()
    load_forecasts()
    yield


app = FastAPI(
    title="UK Wind Generation Forecast Monitor API",
    description=(
        "Day-ahead power procurement analytics for UK National Wind generation. "
        "Scope: Delivery days whose D-1 purchase decision falls in January 2026 (2 Jan 2026 - 1 Feb 2026). "
        "Provides latest forecasts available at day-ahead decision cutoffs, fixed-horizon forecasts, "
        "and quantitative forecast accuracy metrics (MAE, RMSE, bias, percentiles)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local React/Vite development, Docker, and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_date_param(param_val: str, is_end: bool = False) -> datetime:
    """
    Parses a date or datetime string (YYYY-MM-DD or ISO) as explicit UTC.
    If only YYYY-MM-DD is given:
      - is_end=False: starts at 00:00:00 UTC
      - is_end=True: ends at 23:59:59 UTC
    """
    try:
        if "T" in param_val:
            return parse_iso(param_val)
        dt = datetime.strptime(param_val, "%Y-%m-%d")
        if is_end:
            return datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=timezone.utc)
        return datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=timezone.utc)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format '{param_val}'. Use YYYY-MM-DD or ISO8601 (e.g. 2026-01-15T00:00:00Z). Error: {str(e)}",
        )


def validate_date_range(start_dt: datetime, end_dt: datetime):
    """Ensure start_dt <= end_dt."""
    if start_dt > end_dt:
        raise HTTPException(
            status_code=400,
            detail=f"Start date ({start_dt.isoformat()}) must be before or equal to end date ({end_dt.isoformat()}).",
        )


@app.get("/api/health")
def health_check():
    """Health check endpoint confirming API status, record counts, and active scope."""
    actuals = load_actuals()
    forecasts = load_forecasts()
    return {
        "status": "healthy",
        "scope": "Decisions in Jan 2026 (Deliveries 2 Jan - 1 Feb 2026)",
        "actuals_count": len(actuals),
        "forecasts_count": len(forecasts),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


@app.get("/api/dashboard")
def get_dashboard(
    from_date: str = Query(DEFAULT_DELIVERY_START, alias="from", description="Start delivery date (YYYY-MM-DD)"),
    to_date: str = Query(DEFAULT_DELIVERY_END, alias="to", description="End delivery date (YYYY-MM-DD)"),
    focus: str = Query(DEFAULT_FOCUS_DAY, description="Focus delivery day (YYYY-MM-DD)"),
    mode: str = Query("dayahead", pattern="^(dayahead|fixed|day-ahead|horizon)$", description="Mode: 'dayahead' or 'fixed'"),
    cutoff: int = Query(DEFAULT_CUTOFF_HOUR, ge=0, le=23, description="Cutoff hour on D-1 in UTC"),
    horizon: float = Query(DEFAULT_HORIZON_HOURS, ge=0.0, le=48.0, description="Horizon hours for fixed mode"),
):
    """
    Consolidated single-source-of-truth endpoint for the dashboard.
    Returns the complete payload needed by App.jsx in a single call:
      - rows: half-hourly aligned actual, forecast, error, publish, age
      - stats: MAE, RMSE, bias, P90, P99, MAPE
      - coverage: matched, total, noForecast, noActual
      - focus: focus day stats, peak half-hour, asOf publish time, age range
      - daily: 31 delivery days (2 Jan - 1 Feb) for the Hero selector strip
      - histogram: 500 MW bins with overflow bars
      - horizon: 24 two-hour bins scored per forecast vintage
      - ageSpan: [minAge, maxAge]
      - insight: plain-English factual takeaway
    """
    start_dt = parse_date_param(from_date, is_end=False)
    end_dt = parse_date_param(to_date, is_end=True)
    validate_date_range(start_dt, end_dt)

    actuals = load_actuals()
    forecasts = load_forecasts()

    # Determine mode normalization
    is_day_ahead = mode in ["dayahead", "day-ahead"]

    # Build forecast list for the selected range
    if is_day_ahead:
        fc_list = build_day_ahead_forecasts(
            forecasts,
            target_start_dt=start_dt,
            target_end_dt=end_dt,
            cutoff_hour=cutoff,
        )
    else:
        fc_list = build_horizon_forecasts(
            forecasts,
            target_start_dt=start_dt,
            target_end_dt=end_dt,
            horizon_hours=horizon,
        )

    # Filter actuals in range and align
    range_actuals = filter_records_by_time_range(actuals, start_dt, end_dt, key="startTime")
    rows = align_actuals_with_forecasts(range_actuals, fc_list, expand_to_half_hours=True)

    # Compute range metrics
    m = compute_metrics(rows)

    # Compute daily strip across the standard 31-day delivery scope (2 Jan to 1 Feb)
    scope_start_dt = parse_date_param(DEFAULT_DELIVERY_START, is_end=False)
    scope_end_dt = parse_date_param(DEFAULT_DELIVERY_END, is_end=True)
    
    if is_day_ahead:
        scope_fcs = build_day_ahead_forecasts(forecasts, scope_start_dt, scope_end_dt, cutoff_hour=cutoff)
    else:
        scope_fcs = build_horizon_forecasts(forecasts, scope_start_dt, scope_end_dt, horizon_hours=horizon)
    
    scope_acts = filter_records_by_time_range(actuals, scope_start_dt, scope_end_dt, key="startTime")
    scope_aligned = align_actuals_with_forecasts(scope_acts, scope_fcs, expand_to_half_hours=True)
    daily_breakdown = compute_daily_breakdown(scope_aligned)

    # Focus day details
    focus_details = compute_focus_day_details(focus, scope_aligned, forecasts, cutoff_hour=cutoff)

    # Vintage effective-age horizon curve (24 two-hour bins)
    vintage_horizon = compute_vintage_effective_age_horizon(
        forecasts, actuals, start_dt, end_dt, max_age_hours=48, bin_width=2
    )

    return {
        "params": {
            "from": from_date,
            "to": to_date,
            "focus": focus,
            "mode": "dayahead" if is_day_ahead else "fixed",
            "cutoff": cutoff,
            "horizon": horizon,
        },
        "rows": rows,
        "stats": {
            "n": m["matchedPeriods"],
            "mae": m["mae"],
            "rmse": m["rmse"],
            "bias": m["bias"],
            "p50": m["p50"],
            "p90": m["p90"],
            "p99": m["p99"],
            "mape": m["mape"],
        } if m["matchedPeriods"] > 0 else None,
        "coverage": m["coverage"],
        "focus": focus_details,
        "daily": daily_breakdown["daily"],
        "histogram": m["histogram"],
        "horizon": vintage_horizon,
        "ageSpan": m["ageSpan"],
        "insight": m["insight"],
        "reconciliation": daily_breakdown["reconciliation"],
        "empty": len(rows) == 0,
    }


@app.get("/api/actuals")
def get_actuals(
    start: str = Query(DEFAULT_DELIVERY_START, description="Start date (YYYY-MM-DD or ISO)"),
    end: str = Query(DEFAULT_DELIVERY_END, description="End date (YYYY-MM-DD or ISO)"),
):
    """
    Returns actual wind generation (MW) from Elexon FUELHH dataset.
    Resolution: 30-minute settlement periods.
    """
    start_dt = parse_date_param(start, is_end=False)
    end_dt = parse_date_param(end, is_end=True)
    validate_date_range(start_dt, end_dt)

    actuals = load_actuals()
    filtered = filter_records_by_time_range(actuals, start_dt, end_dt, key="startTime")

    return {
        "startDate": format_iso(start_dt),
        "endDate": format_iso(end_dt),
        "count": len(filtered),
        "data": filtered,
    }


@app.get("/api/forecast/day-ahead")
def get_day_ahead_forecast(
    start: str = Query(DEFAULT_DELIVERY_START, description="Start date (YYYY-MM-DD or ISO)"),
    end: str = Query(DEFAULT_DELIVERY_END, description="End date (YYYY-MM-DD or ISO)"),
    cutoff_hour: int = Query(
        DEFAULT_CUTOFF_HOUR, ge=0, le=23,
        description="Decision cutoff hour on Day D-1 in UTC (default 9: 09:00 UTC). Assumption documented."
    ),
):
    """
    For each target delivery startTime on Day D, returns the latest wind forecast published
    on or before the decision cutoff on Day D-1 (default 09:00 UTC on D-1).
    Also includes aligned actuals and error where available for direct charting.
    """
    start_dt = parse_date_param(start, is_end=False)
    end_dt = parse_date_param(end, is_end=True)
    validate_date_range(start_dt, end_dt)

    forecasts = load_forecasts()
    actuals = load_actuals()

    da_forecasts = build_day_ahead_forecasts(
        forecasts,
        target_start_dt=start_dt,
        target_end_dt=end_dt,
        cutoff_hour=cutoff_hour,
        cutoff_minute=0,
        expand_to_half_hours=True,
    )

    filtered_actuals = filter_records_by_time_range(actuals, start_dt, end_dt, key="startTime")
    aligned = align_actuals_with_forecasts(filtered_actuals, da_forecasts, expand_to_half_hours=True)

    return {
        "mode": "day-ahead",
        "startDate": format_iso(start_dt),
        "endDate": format_iso(end_dt),
        "cutoffHour": cutoff_hour,
        "cutoffTimeAssumption": f"Day D-1 at {cutoff_hour:02d}:00 UTC",
        "count": len(da_forecasts),
        "forecasts": da_forecasts,
        "aligned": aligned,
    }


@app.get("/api/forecast/horizon")
def get_horizon_forecast(
    start: str = Query(DEFAULT_DELIVERY_START, description="Start date (YYYY-MM-DD or ISO)"),
    end: str = Query(DEFAULT_DELIVERY_END, description="End date (YYYY-MM-DD or ISO)"),
    hours: float = Query(
        DEFAULT_HORIZON_HOURS, ge=0.0, le=48.0,
        description="Forecast horizon N in hours (latest forecast published <= startTime - N hours)."
    ),
):
    """
    For each target delivery startTime, returns the latest wind forecast published
    at least N hours before the delivery start time (publishTime <= startTime - N hours).
    """
    start_dt = parse_date_param(start, is_end=False)
    end_dt = parse_date_param(end, is_end=True)
    validate_date_range(start_dt, end_dt)

    forecasts = load_forecasts()
    actuals = load_actuals()

    hz_forecasts = build_horizon_forecasts(
        forecasts,
        target_start_dt=start_dt,
        target_end_dt=end_dt,
        horizon_hours=hours,
        expand_to_half_hours=True,
    )

    filtered_actuals = filter_records_by_time_range(actuals, start_dt, end_dt, key="startTime")
    aligned = align_actuals_with_forecasts(filtered_actuals, hz_forecasts, expand_to_half_hours=True)

    return {
        "mode": "horizon",
        "startDate": format_iso(start_dt),
        "endDate": format_iso(end_dt),
        "horizonHours": hours,
        "count": len(hz_forecasts),
        "forecasts": hz_forecasts,
        "aligned": aligned,
    }


@app.get("/api/metrics")
def get_metrics(
    mode: str = Query("day-ahead", pattern="^(day-ahead|horizon|dayahead|fixed)$", description="Mode: 'day-ahead' or 'horizon'"),
    start: str = Query(DEFAULT_DELIVERY_START, description="Start date (YYYY-MM-DD or ISO)"),
    end: str = Query(DEFAULT_DELIVERY_END, description="End date (YYYY-MM-DD or ISO)"),
    cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR, ge=0, le=23, description="Cutoff hour on D-1 in UTC (used when mode='day-ahead')"),
    hours: float = Query(DEFAULT_HORIZON_HOURS, ge=0.0, le=48.0, description="Horizon in hours (used when mode='horizon')"),
):
    """
    Computes quantitative forecast accuracy metrics for the specified mode and date range:
    MAE, RMSE, MAPE (zero-safe), bias (mean signed error), percentiles (P50, P90, P99),
    coverage counts, plain-English takeaway insight, and 500 MW histogram bins.
    """
    start_dt = parse_date_param(start, is_end=False)
    end_dt = parse_date_param(end, is_end=True)
    validate_date_range(start_dt, end_dt)

    actuals = load_actuals()
    forecasts = load_forecasts()

    is_da = mode in ["day-ahead", "dayahead"]
    if is_da:
        fc_list = build_day_ahead_forecasts(
            forecasts,
            target_start_dt=start_dt,
            target_end_dt=end_dt,
            cutoff_hour=cutoff_hour,
        )
    else:
        fc_list = build_horizon_forecasts(
            forecasts,
            target_start_dt=start_dt,
            target_end_dt=end_dt,
            horizon_hours=hours,
        )

    filtered_actuals = filter_records_by_time_range(actuals, start_dt, end_dt, key="startTime")
    aligned = align_actuals_with_forecasts(filtered_actuals, fc_list, expand_to_half_hours=True)
    metrics_result = compute_metrics(aligned)

    return {
        "mode": "day-ahead" if is_da else "horizon",
        "startDate": format_iso(start_dt),
        "endDate": format_iso(end_dt),
        "cutoffHour": cutoff_hour if is_da else None,
        "horizonHours": hours if not is_da else None,
        **metrics_result,
    }


@app.get("/api/metrics/by-horizon")
def get_metrics_by_horizon(
    start: str = Query(DEFAULT_DELIVERY_START, description="Start date (YYYY-MM-DD or ISO)"),
    end: str = Query(DEFAULT_DELIVERY_END, description="End date (YYYY-MM-DD or ISO)"),
    min_horizon: int = Query(0, ge=0, le=48, description="Minimum horizon hours (default 0)"),
    max_horizon: int = Query(48, ge=0, le=48, description="Maximum horizon hours (default 48)"),
    step: int = Query(3, ge=1, le=12, description="Horizon step in hours (default 3)"),
):
    """
    Computes error metrics (MAE, RMSE, bias, P90) across horizons from min_horizon to max_horizon.
    Used to render Chart 2: Forecast Error vs Lead Time (Horizon).
    """
    start_dt = parse_date_param(start, is_end=False)
    end_dt = parse_date_param(end, is_end=True)
    validate_date_range(start_dt, end_dt)

    if min_horizon > max_horizon:
        raise HTTPException(status_code=400, detail="min_horizon cannot exceed max_horizon.")

    actuals = load_actuals()
    forecasts = load_forecasts()
    filtered_actuals = filter_records_by_time_range(actuals, start_dt, end_dt, key="startTime")

    horizons = list(range(min_horizon, max_horizon + 1, step))
    results = compute_metrics_by_horizon(
        filtered_actuals,
        forecasts,
        target_start_dt=start_dt,
        target_end_dt=end_dt,
        horizons=horizons,
    )

    return {
        "startDate": format_iso(start_dt),
        "endDate": format_iso(end_dt),
        "horizonsEvaluated": len(horizons),
        "data": results,
    }


@app.get("/api/daily")
def get_daily_table(
    start: str = Query(DEFAULT_DELIVERY_START, description="Start date (YYYY-MM-DD)"),
    end: str = Query(DEFAULT_DELIVERY_END, description="End date (YYYY-MM-DD)"),
    cutoff_hour: int = Query(DEFAULT_CUTOFF_HOUR, ge=0, le=23, description="Cutoff hour on D-1 in UTC"),
):
    """
    Returns day-by-day table of mean actual, mean forecast, bias, MAE, max actual,
    and exact mathematical reconciliation audit metrics.
    """
    start_dt = parse_date_param(start, is_end=False)
    end_dt = parse_date_param(end, is_end=True)
    validate_date_range(start_dt, end_dt)

    actuals = load_actuals()
    forecasts = load_forecasts()

    da_fcs = build_day_ahead_forecasts(forecasts, start_dt, end_dt, cutoff_hour=cutoff_hour)
    range_actuals = filter_records_by_time_range(actuals, start_dt, end_dt, key="startTime")
    aligned = align_actuals_with_forecasts(range_actuals, da_fcs, expand_to_half_hours=True)

    breakdown = compute_daily_breakdown(aligned)
    return {
        "startDate": format_iso(start_dt),
        "endDate": format_iso(end_dt),
        "cutoffHour": cutoff_hour,
        **breakdown,
    }
