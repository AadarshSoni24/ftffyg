"""
backend/tests/test_forecast_engine.py
Unit tests for pure domain logic: day-ahead cutoff selection, horizon filtering,
metrics calculation (MAE, RMSE, MAPE zero-safety, bias, percentiles), and missing data handling.
"""

import pytest
from datetime import datetime
from backend.forecast_engine import (
    parse_iso,
    format_iso,
    get_latest_forecast_for_target,
    build_day_ahead_forecasts,
    build_horizon_forecasts,
    align_actuals_with_forecasts,
    compute_metrics,
    compute_metrics_by_horizon,
)


def test_iso_parsing_and_formatting():
    """Verify ISO8601 parsing handles UTC Z and converts to naive UTC."""
    dt_str = "2026-01-15T09:30:00Z"
    dt = parse_iso(dt_str)
    assert dt.year == 2026
    assert dt.month == 1
    assert dt.day == 15
    assert dt.hour == 9
    assert dt.minute == 30
    assert format_iso(dt) == dt_str


def test_get_latest_forecast_before_cutoff():
    """
    Given forecasts published at multiple times for the same target,
    verify that it selects the latest published before or at the cutoff,
    and ignores any published after the cutoff.
    """
    target = "2026-01-10T12:00:00Z"
    forecasts = [
        {"startTime": target, "publishTime": "2026-01-08T06:00:00Z", "generation": 5000.0},
        {"startTime": target, "publishTime": "2026-01-09T08:30:00Z", "generation": 5500.0},  # Before 09:00
        {"startTime": target, "publishTime": "2026-01-09T09:00:00Z", "generation": 5600.0},  # Exactly at 09:00
        {"startTime": target, "publishTime": "2026-01-09T09:15:00Z", "generation": 5900.0},  # After 09:00 cutoff
        {"startTime": target, "publishTime": "2026-01-10T06:00:00Z", "generation": 6200.0},  # Same day
    ]

    cutoff_dt = datetime(2026, 1, 9, 9, 0, 0)
    chosen = get_latest_forecast_for_target(forecasts, cutoff_dt)
    assert chosen is not None
    # Must pick the one at 09:00:00, NOT the 09:15:00 or 10th
    assert chosen["publishTime"] == "2026-01-09T09:00:00Z"
    assert chosen["generation"] == 5600.0


def test_missing_forecast_before_cutoff():
    """If all forecasts were published after the decision cutoff, returns None."""
    target = "2026-01-10T12:00:00Z"
    forecasts = [
        {"startTime": target, "publishTime": "2026-01-09T10:00:00Z", "generation": 6000.0},
    ]
    cutoff_dt = datetime(2026, 1, 9, 9, 0, 0)
    chosen = get_latest_forecast_for_target(forecasts, cutoff_dt)
    assert chosen is None


def test_day_ahead_forecast_builder():
    """
    Verify build_day_ahead_forecasts correctly calculates cutoff as D-1 09:00 UTC
    for delivery day D.
    """
    forecasts = [
        # Target: 2026-01-02 14:00 (Delivery day D = Jan 2, cutoff = Jan 1 09:00 UTC)
        {"startTime": "2026-01-02T14:00:00Z", "publishTime": "2026-01-01T08:00:00Z", "generation": 7000.0},
        {"startTime": "2026-01-02T14:00:00Z", "publishTime": "2026-01-01T10:00:00Z", "generation": 7500.0},  # After cutoff
    ]

    res = build_day_ahead_forecasts(
        forecasts,
        target_start_dt=datetime(2026, 1, 2, 0, 0, 0),
        target_end_dt=datetime(2026, 1, 2, 23, 59, 59),
        cutoff_hour=9,
    )

    assert len(res) == 1
    assert res[0]["startTime"] == "2026-01-02T14:00:00Z"
    assert res[0]["publishTime"] == "2026-01-01T08:00:00Z"
    assert res[0]["generation"] == 7000.0
    assert res[0]["cutoffTime"] == "2026-01-01T09:00:00Z"


def test_horizon_forecast_builder():
    """
    Verify horizon logic: for target startTime and horizon H=12,
    cutoff is target - 12 hours.
    """
    target = "2026-01-05T18:00:00Z"
    forecasts = [
        {"startTime": target, "publishTime": "2026-01-05T05:00:00Z", "generation": 8000.0},  # 13h before (eligible)
        {"startTime": target, "publishTime": "2026-01-05T06:00:00Z", "generation": 8200.0},  # Exactly 12h before (eligible)
        {"startTime": target, "publishTime": "2026-01-05T07:00:00Z", "generation": 8500.0},  # 11h before (ineligible)
    ]

    res = build_horizon_forecasts(
        forecasts,
        target_start_dt=datetime(2026, 1, 5, 0, 0, 0),
        target_end_dt=datetime(2026, 1, 5, 23, 59, 59),
        horizon_hours=12.0,
    )

    assert len(res) == 1
    assert res[0]["generation"] == 8200.0
    assert res[0]["publishTime"] == "2026-01-05T06:00:00Z"


def test_align_actuals_and_forecasts_half_hourly():
    """
    Verify that an hourly WINDFOR forecast at HH:00 is mapped
    to both HH:00 and HH:30 FUELHH actuals when expand_to_half_hours=True.
    """
    actuals = [
        {"startTime": "2026-01-01T10:00:00Z", "settlementDate": "2026-01-01", "settlementPeriod": 21, "generation": 10000.0},
        {"startTime": "2026-01-01T10:30:00Z", "settlementDate": "2026-01-01", "settlementPeriod": 22, "generation": 10200.0},
    ]
    forecasts = [
        {"startTime": "2026-01-01T10:00:00Z", "publishTime": "2025-12-31T08:00:00Z", "generation": 10500.0},
    ]

    aligned = align_actuals_with_forecasts(actuals, forecasts, expand_to_half_hours=True)
    assert len(aligned) == 2

    # HH:00
    assert aligned[0]["actual"] == 10000.0
    assert aligned[0]["forecast"] == 10500.0
    assert aligned[0]["error"] == 500.0
    assert aligned[0]["absoluteError"] == 500.0

    # HH:30 mapped to 10:00 forecast
    assert aligned[1]["actual"] == 10200.0
    assert aligned[1]["forecast"] == 10500.0
    assert aligned[1]["error"] == 300.0
    assert aligned[1]["absoluteError"] == 300.0


def test_metrics_calculation_mathematical_correctness():
    """
    Verify MAE, RMSE, bias, MAPE, and percentiles on exact known numbers.
    Pairs:
      actual=1000, forecast=1200 -> error = +200, abs = 200
      actual=2000, forecast=1900 -> error = -100, abs = 100
      actual=3000, forecast=3300 -> error = +300, abs = 300
    Expected:
      errors = [200, -100, 300]
      abs_errors = [200, 100, 300] -> sorted = [100, 200, 300]
      MAE = (200 + 100 + 300) / 3 = 200.0 MW
      RMSE = sqrt((40000 + 10000 + 90000) / 3) = sqrt(140000 / 3) = sqrt(46666.67) = 216.0 MW
      Bias = (200 - 100 + 300) / 3 = +133.3 MW
      MAPE = (200/1000 + 100/2000 + 300/3000) / 3 = (0.2 + 0.05 + 0.1) / 3 = 0.35 / 3 = 11.67%
      P50 = 200.0 MW
    """
    aligned = [
        {"actual": 1000.0, "forecast": 1200.0, "error": 200.0, "absoluteError": 200.0},
        {"actual": 2000.0, "forecast": 1900.0, "error": -100.0, "absoluteError": 100.0},
        {"actual": 3000.0, "forecast": 3300.0, "error": 300.0, "absoluteError": 300.0},
    ]

    metrics = compute_metrics(aligned)
    assert metrics["totalPeriods"] == 3
    assert metrics["matchedPeriods"] == 3
    assert metrics["coveragePct"] == 100.0
    assert metrics["mae"] == 200.0
    assert metrics["rmse"] == 216.0
    assert metrics["bias"] == 133.3
    assert metrics["mape"] == 11.67
    assert metrics["p50"] == 200.0
    assert "too high" in metrics["insight"]


def test_zero_safe_mape():
    """
    Verify MAPE calculation safely ignores zero or near-zero generation actuals (< 50 MW)
    without raising DivisionByZero or returning inf/NaN.
    """
    aligned = [
        {"actual": 0.0, "forecast": 100.0, "error": 100.0, "absoluteError": 100.0},  # actual = 0
        {"actual": 20.0, "forecast": 80.0, "error": 60.0, "absoluteError": 60.0},    # actual < 50
        {"actual": 1000.0, "forecast": 1100.0, "error": 100.0, "absoluteError": 100.0},  # actual = 1000 -> 10%
    ]

    metrics = compute_metrics(aligned)
    assert metrics["mape"] == 10.0  # Only the eligible pair is evaluated


def test_empty_and_missing_data_resilience():
    """Verify that empty datasets or completely missing forecasts do not crash."""
    empty_metrics = compute_metrics([])
    assert empty_metrics["totalPeriods"] == 0
    assert empty_metrics["matchedPeriods"] == 0
    assert empty_metrics["coveragePct"] == 0.0
    assert empty_metrics["mae"] is None
    assert empty_metrics["rmse"] is None

    unmatched = [
        {"actual": 5000.0, "forecast": None, "error": None, "absoluteError": None},
        {"actual": None, "forecast": 4000.0, "error": None, "absoluteError": None},
    ]
    unmatched_metrics = compute_metrics(unmatched)
    assert unmatched_metrics["totalPeriods"] == 2
    assert unmatched_metrics["matchedPeriods"] == 0
    assert unmatched_metrics["coveragePct"] == 0.0
    assert unmatched_metrics["mae"] is None
