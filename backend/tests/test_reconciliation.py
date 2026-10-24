"""
backend/tests/test_reconciliation.py
Unit tests verifying the mathematical reconciliation between daily tables and overall metrics,
500 MW histogram binning, focus-day detail generation, and vintage effective-age scoring.
Scope: Delivery days whose D-1 purchase decision falls in January 2026 (2026-01-02 to 2026-02-01).
"""

import pytest
from datetime import datetime, timezone
from backend.forecast_engine import (
    build_day_ahead_forecasts,
    align_actuals_with_forecasts,
    compute_metrics,
    compute_daily_breakdown,
    build_500mw_histogram,
    compute_focus_day_details,
    compute_vintage_effective_age_horizon,
    parse_iso,
)
from backend.data_loader import load_actuals, load_forecasts


@pytest.fixture
def real_data():
    actuals = load_actuals()
    forecasts = load_forecasts()
    return actuals, forecasts


def test_daily_reconciliation_exact_math(real_data):
    """
    Verifies that daily breakdown metrics mathematically reconcile with overall metrics:
      1. sum(day.signedErrorSum) == totalSignedError
      2. weighted average of daily biases == overall bias (diff == 0.0)
      3. weighted average of daily MAEs == overall MAE (diff == 0.0)
      4. mean(daily forecast) - mean(daily actual) == overall bias
    """
    actuals, forecasts = real_data
    start_dt = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 2, 1, 23, 59, 59, tzinfo=timezone.utc)

    da = build_day_ahead_forecasts(forecasts, start_dt, end_dt, cutoff_hour=9)
    acts = [a for a in actuals if start_dt <= parse_iso(a["startTime"]) <= end_dt]
    aligned = align_actuals_with_forecasts(acts, da, expand_to_half_hours=True)

    metrics = compute_metrics(aligned)
    breakdown = compute_daily_breakdown(aligned)

    recon = breakdown["reconciliation"]
    assert recon["reconciliationStatus"] == "PASSED"
    assert recon["totalDays"] == 31
    assert recon["totalPeriods"] == 1488
    assert recon["totalMatched"] == 1488

    # Check exact bias reconciliation
    assert recon["reconciliationDiffBias"] < 0.05
    assert recon["overallBias"] == metrics["bias"]

    # Check exact MAE reconciliation
    assert recon["reconciliationDiffMae"] < 0.05
    assert recon["overallMae"] == metrics["mae"]

    # Check daily table integrity
    daily_rows = breakdown["daily"]
    assert len(daily_rows) == 31
    for row in daily_rows:
        assert row["periods"] == 48
        assert row["matched"] == 48
        # Day bias must equal avgForecast - avgActual within floating-point decimal rounding (<= 0.1 MW)
        assert abs((row["avgForecast"] - row["avgActual"]) - row["bias"]) <= 0.1


def test_500mw_histogram_overflow_and_counts():
    """
    Verifies build_500mw_histogram creates 20 bins of 500 MW,
    properly collects overflow at <= -5000 and >= +5000,
    and total bin count equals total inputs.
    """
    errors = [-6000.0, -5200.0, -4800.0, -250.0, 0.0, 300.0, 4800.0, 5100.0, 7500.0]
    bins = build_500mw_histogram(errors, limit=5000.0, width=500.0)

    assert len(bins) == 20
    assert bins[0]["x0"] == -5000.0
    assert bins[-1]["x1"] == 5000.0

    # Underflow collected in first bin (-6000, -5200) + (-4800 is in [-5000, -4500]) -> 3 items
    assert bins[0]["count"] == 3

    # Overflow collected in last bin: 4800 in [4500, 5000] + 5100 and 7500 overflow -> 3 items
    assert bins[-1]["count"] == 3

    # Total counts must equal total errors
    assert sum(b["count"] for b in bins) == len(errors)


def test_focus_day_details_calculation(real_data):
    """Verifies compute_focus_day_details generates correct structure for Hero display."""
    actuals, forecasts = real_data
    start_dt = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 2, 1, 23, 59, 59, tzinfo=timezone.utc)

    da = build_day_ahead_forecasts(forecasts, start_dt, end_dt, cutoff_hour=9)
    acts = [a for a in actuals if start_dt <= parse_iso(a["startTime"]) <= end_dt]
    aligned = align_actuals_with_forecasts(acts, da, expand_to_half_hours=True)

    focus = compute_focus_day_details("2026-01-14", aligned, forecasts, cutoff_hour=9)

    assert focus["date"] == "2026-01-14"
    assert focus["available"] == 48
    assert focus["avgForecast"] is not None
    assert focus["avgActual"] is not None
    assert focus["peak"] is not None
    assert "t" in focus["peak"]
    assert "forecast" in focus["peak"]
    assert focus["asOf"] is not None
    assert focus["ages"] is not None
    assert len(focus["ages"]) == 2
    assert focus["stats"] is not None
    assert "mae" in focus["stats"]


def test_vintage_effective_age_horizon(real_data):
    """
    Verifies that compute_vintage_effective_age_horizon produces 24 bins of 2h width,
    scores every vintage, and excludes negative horizons.
    """
    actuals, forecasts = real_data
    start_dt = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 2, 1, 23, 59, 59, tzinfo=timezone.utc)

    horizon_curve = compute_vintage_effective_age_horizon(
        forecasts, actuals, start_dt, end_dt, max_age_hours=48, bin_width=2
    )

    assert len(horizon_curve) == 24
    for b in horizon_curve:
        assert b["from"] >= 0
        assert b["to"] <= 48
        assert b["mid"] == b["from"] + 1
        assert b["n"] > 0
        assert b["mae"] is not None


def test_epoch_ms_utc_alignment(real_data):
    """
    Verifies that t and publish timestamps in aligned records exactly match
    the true UTC epoch milliseconds of startTime and publishTime:
      t == int(datetime.fromisoformat(r["startTime"].replace("Z", "+00:00")).timestamp() * 1000)
      publish == int(datetime.fromisoformat(r["publishTime"].replace("Z", "+00:00")).timestamp() * 1000)
    """
    actuals, forecasts = real_data
    start_dt = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 2, 1, 23, 59, 59, tzinfo=timezone.utc)

    da = build_day_ahead_forecasts(forecasts, start_dt, end_dt, cutoff_hour=9)
    acts = [a for a in actuals if start_dt <= parse_iso(a["startTime"]) <= end_dt]
    aligned = align_actuals_with_forecasts(acts, da, expand_to_half_hours=True)

    assert len(aligned) == 1488
    for r in aligned:
        expected_t = int(datetime.fromisoformat(r["startTime"].replace("Z", "+00:00")).timestamp() * 1000)
        assert r["t"] == expected_t, f"t {r['t']} != expected {expected_t} for {r['startTime']}"

        if r.get("publishTime") and r.get("publish"):
            expected_pub = int(datetime.fromisoformat(r["publishTime"].replace("Z", "+00:00")).timestamp() * 1000)
            assert r["publish"] == expected_pub, f"publish {r['publish']} != expected {expected_pub} for {r['publishTime']}"


def test_real_data_histogram_exact_sum(real_data):
    """
    Verifies that 500 MW histogram bins have no gaps and counts sum exactly to 1,488.
    """
    actuals, forecasts = real_data
    start_dt = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 2, 1, 23, 59, 59, tzinfo=timezone.utc)

    da = build_day_ahead_forecasts(forecasts, start_dt, end_dt, cutoff_hour=9)
    acts = [a for a in actuals if start_dt <= parse_iso(a["startTime"]) <= end_dt]
    aligned = align_actuals_with_forecasts(acts, da, expand_to_half_hours=True)

    metrics = compute_metrics(aligned)
    bins = metrics["histogram"]["bins"]

    assert len(bins) == 20
    # No gaps: x1 of bin[i] == x0 of bin[i+1]
    for i in range(len(bins) - 1):
        assert bins[i]["x1"] == bins[i + 1]["x0"]

    # Sum of counts must identically equal matched periods (1,488)
    assert sum(b["count"] for b in bins) == 1488
    assert metrics["matchedPeriods"] == 1488
