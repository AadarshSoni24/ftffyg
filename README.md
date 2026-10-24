# UK National Wind Generation Forecast Monitor

An operational web application and quantitative analytics platform tailored for a UK electricity utility's Day-Ahead power trading and procurement desk. The platform evaluates UK National Wind generation forecasts (`WINDFOR`) against actual transmission-system metered wind generation (`FUELHH`, `fuelType='WIND'`) from Elexon BMRS, empowering procurement teams to quantify volume exposure, evaluate systematic bias, inspect day-by-day error concentrations, and monitor forecast evolution across 0 to 48 hours lead time.

## Live Application
- **Production URL:** https://ftffyg.vercel.app

## Scope and Assumptions
- **Delivery Range:** Delivery days 2 January 2026 00:00 UTC through 1 February 2026 23:30 UTC (all delivery days whose Day $D-1$ procurement decisions occurred in January 2026).
- **Day-Ahead Decision Cutoff:** Default 09:00 UTC on Day $D-1$ (configurable to 06:00, 09:00, 12:00, or 15:00 UTC to match auction clearing gates).
- **Selection Rule:** For each target delivery half-hour, selects the latest forecast vintage published at or prior to the Day $D-1$ cutoff (`publishTime <= cutoff`).
- **Error Definition:** $\text{Error} = \text{Forecast} - \text{Actual}$. Positive values indicate over-forecasting (contracting shortfall); negative values indicate under-forecasting.
- **Temporal Alignment:** Hourly `WINDFOR` forecasts are mapped to 30-minute settlement periods (half-hours 1 & 2 inherit the hour forecast).
- **Timezone:** All timestamps are parsed, processed, and served in explicit UTC.
- **Offline Data Bundling:** Datasets are fetched once offline and committed as clean CSVs in `backend/data/`. The running application never calls Elexon APIs at runtime.
- **Metering Scope:** Metered generation covers Great Britain transmission-system metered wind only (embedded distribution wind is excluded per FUELHH scope).

## Key Results (Full Evaluation Range)
Evaluating all 31 delivery days (2 Jan – 1 Feb 2026) at the standard 09:00 UTC decision cutoff yields:
- **Mean Absolute Error (MAE):** 2,042.0 MW
- **Root Mean Squared Error (RMSE):** 2,509.1 MW
- **Mean Bias ($\text{Forecast} - \text{Actual}$):** +1,747.9 MW
- **P90 Absolute Error:** 4,140.1 MW
- **Coverage:** Exactly 1,488 of 1,488 settlement periods matched (100.0% coverage).
- **Directional Consistency:** Day-ahead forecast was too high on 27 of 31 delivery days (87.1% of days; 84.7% of individual settlement periods).
Causes of the bias were not tested and are listed as hypotheses in `docs/FINDINGS.md`.

## Files and Directories
```text
.
├── .env.example                                      # Environment variable defaults
├── .gitignore                                        # Git exclusions for dependencies and caches
├── README.md                                         # Project documentation and operational guide
├── requirements.txt                                  # Root Python dependencies for cloud deployment
├── docker-compose.yml                                # Multi-container production deployment config
├── vercel.json                                       # Vercel serverless routing and bundle rules
├── api/
│   └── index.py                                      # ASGI gateway exporting FastAPI app for Vercel
├── backend/
│   ├── Dockerfile                                    # FastAPI container configuration (TZ=UTC)
│   ├── __init__.py                                   # Python module initialization
│   ├── data_loader.py                                # CSV data ingestion with memory caching
│   ├── forecast_engine.py                            # Pure-function quantitative calculation engine
│   ├── main.py                                       # FastAPI REST endpoints and validation
│   ├── requirements.txt                              # Backend Python package requirements
│   ├── data/
│   │   ├── actuals.csv                               # Metered wind generation actuals (FUELHH)
│   │   └── forecasts.csv                             # National wind generation forecasts (WINDFOR)
│   └── tests/
│       ├── test_api.py                               # FastAPI endpoint status, bounds and schemas
│       ├── test_forecast_engine.py                   # Engine logic, cutoff, and histogram tests
│       └── test_reconciliation.py                   # Mathematical reconciliation and epoch tests
├── docs/
│   ├── FINDINGS.md                                   # Empirical findings and segregated hypotheses
│   └── daily_table.csv                               # Canonical 31-day daily metrics breakdown
├── frontend/
│   ├── .gitignore                                    # Frontend Git exclusion rules
│   ├── Dockerfile                                    # Multi-stage Nginx container build (TZ=UTC)
│   ├── index.html                                    # Single-page application HTML entrypoint
│   ├── nginx.conf                                    # Nginx reverse proxy configuration (port 80)
│   ├── package.json                                  # Frontend NPM dependencies and build scripts
│   ├── package-lock.json                             # Exact NPM dependency tree lockfile
│   ├── tsconfig.json                                 # TypeScript compiler configuration
│   ├── vite.config.ts                                # Vite bundler configuration
│   ├── public/
│   │   └── favicon.svg                               # Wind turbine SVG favicon
│   └── src/
│       ├── App.jsx                                   # Top-level React dashboard application
│       ├── api.js                                    # API client communicating with FastAPI
│       ├── index.css                                 # Design tokens and Tailwind CSS rules
│       ├── main.tsx                                  # React DOM bootstrap entrypoint
│       ├── vite-env.d.ts                             # Vite TypeScript environment declarations
│       ├── components/
│       │   ├── Controls.jsx                          # Horizon and date range selector controls
│       │   ├── Footer.jsx                            # Methodology and Elexon BMRS citations
│       │   ├── Header.jsx                            # Header bar with real-time UTC clocks
│       │   ├── Hero.jsx                              # 31-day thumbnail strip and focus metrics
│       │   ├── MainChart.jsx                         # Recharts time-series chart with dynamic ceiling
│       │   ├── Metrics.jsx                           # KPI summary cards and evaluation summary
│       │   ├── States.jsx                            # Skeleton loading and error boundary states
│       │   ├── SupportCharts.jsx                     # 500 MW histogram and horizon evolution curve
│       │   └── WindField.jsx                         # Ambient particle background canvas
│       └── lib/
│           ├── analysis.js                           # UI display constants and label helpers
│           └── format.js                             # Number and date formatting utilities
└── scripts/
    ├── fetch_data.py                                 # Offline pipeline to fetch Elexon CSV datasets
    └── independent_pandas_validation.py              # Standalone pandas script verifying 40 samples
```

## How to Run

### (a) With Docker (Recommended)
```bash
docker compose up --build
```
- **Web Dashboard:** http://localhost:3000
- **FastAPI Interactive Docs:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/api/health

### (b) Without Docker
**1. Backend:**
```bash
python -m venv venv
# Linux/macOS: source venv/bin/activate | Windows: .\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
**2. Frontend (in a second terminal):**
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 in your browser.

### (c) Automated Tests & Independent Validation
```bash
# Run 25-item test suite
python -m pytest backend/tests/ -v

# Run 40-sample independent pandas cross-check (no engine imports)
python scripts/independent_pandas_validation.py
```

### (d) Re-fetching Data
```bash
python scripts/fetch_data.py
```
Pulls raw `FUELHH` and `WINDFOR` streams from Elexon BMRS API, validates records, and writes updated CSVs to `backend/data/`.

## API Reference
| Endpoint | Method | Key Parameters | Description & Example Call |
|:---|:---:|:---|:---|
| `/api/health` | GET | None | API status and record counts: `curl http://127.0.0.1:8000/api/health` |
| `/api/dashboard` | GET | `from`, `to`, `focus`, `mode`, `cutoff`, `horizon` | Consolidated payload: `curl "http://127.0.0.1:8000/api/dashboard?from=2026-01-02&to=2026-02-01"` |
| `/api/actuals` | GET | `start`, `end` | Half-hourly actuals (MW): `curl "http://127.0.0.1:8000/api/actuals?start=2026-01-02&end=2026-01-03"` |
| `/api/forecast/day-ahead` | GET | `start`, `end`, `cutoff_hour` | D-1 forecast series: `curl "http://127.0.0.1:8000/api/forecast/day-ahead?start=2026-01-02&end=2026-01-03"` |
| `/api/forecast/horizon` | GET | `start`, `end`, `hours` | Fixed-horizon series: `curl "http://127.0.0.1:8000/api/forecast/horizon?start=2026-01-02&end=2026-01-03&hours=24"` |
| `/api/metrics` | GET | `start`, `end`, `mode`, `cutoff_hour`, `hours` | Summary statistics: `curl "http://127.0.0.1:8000/api/metrics?start=2026-01-02&end=2026-02-01"` |
| `/api/metrics/by-horizon` | GET | `start`, `end`, `min_horizon`, `max_horizon`, `step` | Horizon progression: `curl "http://127.0.0.1:8000/api/metrics/by-horizon?start=2026-01-02&end=2026-02-01"` |
| `/api/daily` | GET | `start`, `end`, `cutoff_hour` | 31-day table with audit: `curl "http://127.0.0.1:8000/api/daily?start=2026-01-02&end=2026-02-01"` |

## Architecture in 5 Lines
1. **Frontend:** React 19 single-page dashboard built with Vite, Tailwind CSS, and Recharts, performing display and formatting only.
2. **Backend:** FastAPI application acting as the single source of truth for all quantitative calculations, percentiles, and histograms.
3. **Engine:** Pure-function calculation core in `backend/forecast_engine.py` with zero side-effects and exact daily mathematical reconciliation.
4. **Validation:** Pytest test suite enforcing inclusive date boundaries (2 days = 96 rows), contiguous histogram bins, and UTC epoch timestamps.
5. **Deployment:** Multi-container Docker composition (Nginx reverse proxy on port 80/3000) and Vercel serverless functions.

## Deployment on Vercel
The repository deploys directly on Vercel:
- **Serverless API:** `api/index.py` bridges the FastAPI application to Vercel Serverless Functions.
- **Routing & Bundling:** `vercel.json` routes `/api/(.*)` to `api/index.py`, `/assets/(.*)` to built static assets, and includes `backend/**` in the serverless bundle so bundled CSV data files are immediately available.
- **Relative Client:** `frontend/src/api.js` defaults to relative `/api/*` endpoints when `VITE_API_URL` is omitted, eliminating CORS and cross-domain configuration.

## Testing and Validation
- **Unit & Integration Tests:** 25 pytest test cases verifying API response schemas, cutoff rules, invalid date handling, zero-safe MAPE, and UTC epoch alignment.
- **Mathematical Reconciliation Proof:** Tests verify that weighted daily mean bias and MAE reconcile exactly with aggregate figures:
  $$\sum \text{Signed Error} = \text{Overall Error},\quad \text{Weighted Mean Daily Bias} = \text{Overall Bias} = +1,747.9\text{ MW}\quad (\Delta = 0.000000\text{ MW})$$
- **Contiguous Histogram:** Validates 20 contiguous 500 MW bins with overflow bars, strictly summing to 1,488 settlement periods without gaps.
- **Independent Cross-Check:** `scripts/independent_pandas_validation.py` uses direct pandas routines (no engine imports) across 40 sample half-hours to confirm 100.0% matching actuals, forecasts, and publish times.

## Limitations and Next Steps
- **Untested Hypotheses:** Physical explanations for the +1,748 MW bias (e.g., transmission metering boundaries, high-wind curtailment, turbine cut-out) are unverified domain hypotheses documented in `docs/FINDINGS.md`.
- **Deterministic Forecasts:** Evaluates single-point forecasts; probabilistic quantiles and ensemble spreads are not currently available in WINDFOR feeds.
- **Hindcast Suppression:** Historical assimilation rows with negative lead times ($t_{\text{publish}} > t_{\text{target}}$) are filtered out to prevent data leakage.
- **Future Roadmap:** Add real-time intraday forecast drift visualization tracking consecutive publish runs for individual settlement periods.

## Attributions & Credits
- **AI tools used:** Antigravity (code assistance), Figma Make (UI design base).
- **UI design base:** built by a friend.
