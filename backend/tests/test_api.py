"""
backend/tests/test_api.py
Integration tests for FastAPI endpoints:
  - GET /api/health
  - GET /api/actuals
  - GET /api/forecast/day-ahead
  - GET /api/forecast/horizon
  - GET /api/metrics
  - GET /api/metrics/by-horizon
  - Validation error handling (400, 422)
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["actuals_count"] > 0
    assert data["forecasts_count"] > 0


def test_get_actuals_january():
    response = client.get("/api/actuals?start=2026-01-01&end=2026-01-02")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["count"] > 0
    # Two days of 48 half-hours = 96 half-hours
    assert data["count"] == 96
    first = data["data"][0]
    assert "startTime" in first
    assert "generation" in first
    assert first["generation"] is not None


def test_get_day_ahead_forecast():
    response = client.get("/api/forecast/day-ahead?start=2026-01-05&end=2026-01-06&cutoff_hour=9")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "day-ahead"
    assert data["cutoffHour"] == 9
    # Two inclusive delivery days = 96 half-hours
    assert data["count"] == 96
    assert len(data["forecasts"]) == 96
    assert len(data["aligned"]) == 96
    first_aligned = data["aligned"][0]
    assert "actual" in first_aligned
    assert "forecast" in first_aligned
    assert "error" in first_aligned


def test_get_horizon_forecast():
    response = client.get("/api/forecast/horizon?start=2026-01-10&end=2026-01-11&hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "horizon"
    assert data["horizonHours"] == 24.0
    # Two inclusive delivery days = 96 half-hours
    assert data["count"] == 96
    assert len(data["forecasts"]) == 96
    assert len(data["aligned"]) == 96


def test_inclusive_two_days_all_endpoints():
    """
    Verifies that start/end are strictly inclusive across all endpoints:
    Querying 2 days (Jan 2 - Jan 3) yields exactly 96 rows everywhere.
    """
    start = "2026-01-02"
    end = "2026-01-03"

    # Actuals
    r_act = client.get(f"/api/actuals?start={start}&end={end}")
    assert r_act.status_code == 200
    assert r_act.json()["count"] == 96

    # Day-ahead
    r_da = client.get(f"/api/forecast/day-ahead?start={start}&end={end}&cutoff_hour=9")
    assert r_da.status_code == 200
    assert r_da.json()["count"] == 96
    assert len(r_da.json()["aligned"]) == 96

    # Horizon
    r_hz = client.get(f"/api/forecast/horizon?start={start}&end={end}&hours=24")
    assert r_hz.status_code == 200
    assert r_hz.json()["count"] == 96
    assert len(r_hz.json()["aligned"]) == 96

    # Metrics
    r_m = client.get(f"/api/metrics?start={start}&end={end}&mode=day-ahead&cutoff_hour=9")
    assert r_m.status_code == 200
    assert r_m.json()["totalPeriods"] == 96
    assert r_m.json()["matchedPeriods"] == 96

    # Daily table
    r_d = client.get(f"/api/daily?start={start}&end={end}&cutoff_hour=9")
    assert r_d.status_code == 200
    assert len(r_d.json()["daily"]) == 2
    assert r_d.json()["reconciliation"]["totalPeriods"] == 96

    # Dashboard endpoint
    r_dash = client.get(f"/api/dashboard?from={start}&to={end}&focus={start}&mode=dayahead&cutoff=9")
    assert r_dash.status_code == 200
    assert len(r_dash.json()["rows"]) == 96
    assert r_dash.json()["stats"]["n"] == 96


def test_get_metrics_day_ahead():
    response = client.get("/api/metrics?mode=day-ahead&start=2026-01-01&end=2026-01-31&cutoff_hour=9")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "day-ahead"
    assert data["mae"] is not None
    assert data["rmse"] is not None
    assert data["bias"] is not None
    assert data["p90"] is not None
    assert data["coveragePct"] > 95.0
    assert "insight" in data
    assert len(data["errorDistribution"]) > 0


def test_get_metrics_by_horizon():
    response = client.get("/api/metrics/by-horizon?start=2026-01-01&end=2026-01-07&min_horizon=0&max_horizon=24&step=6")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 5  # 0, 6, 12, 18, 24
    for item in data["data"]:
        assert "horizonHours" in item
        assert "mae" in item
        assert "rmse" in item
        assert "p90" in item


def test_invalid_date_range_error():
    # start after end
    response = client.get("/api/actuals?start=2026-01-15&end=2026-01-05")
    assert response.status_code == 400
    assert "must be before or equal" in response.json()["detail"]


def test_invalid_date_format():
    response = client.get("/api/actuals?start=invalid-date&end=2026-01-31")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


def test_invalid_cutoff_hour():
    response = client.get("/api/forecast/day-ahead?cutoff_hour=25")
    assert response.status_code == 422  # FastAPI validation error
