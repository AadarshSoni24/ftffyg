# UK National Wind Generation Forecast Monitor

An operational web application and quantitative analytics platform tailored for a UK electricity utility's Day-Ahead power trading and procurement desk.

The application evaluates UK National Wind generation forecasts (`WINDFOR`) against actual transmission-system metered wind output (`FUELHH`, `fuelType='WIND'`) from Elexon BMRS. It empowers power traders and procurement managers to evaluate forecast accuracy, quantify systematic volume risks, inspect day-by-day error concentrations, and monitor forecast evolution curves across 0 to 48 hours lead time.

---

## Attributions & Credits
- **AI tools used:** Antigravity, Figma Make (UI design base)
- **UI design/base:** built by a friend, no name

---

## Deployed Application
- **Live URL:** [https://gridbricks-wind-monitor.vercel.app](https://gridbricks-wind-monitor.vercel.app) *(Deployment Link Placeholder)*

---

## Key Assumptions & Scope Boundaries

1. **Day-Ahead Decision Cutoff (09:00 UTC on Day $D-1$):**
   - By UK power market design, physical day-ahead notification and exchange auction orders close late morning on Day $D-1$.
   - The platform applies a standard operational baseline assumption of **09:00 UTC on Day $D-1$**. For each delivery settlement period on Day $D$, the trading desk can only access the latest forecast vintage published at or prior to this cutoff.
2. **Decision-Based Scope (2 January 2026 – 1 February 2026):**
   - Covers all electricity delivery days whose Day $D-1$ procurement decisions occurred in calendar month January 2026 (1 January 2026 09:00 UTC through 31 January 2026 09:00 UTC).
   - Delivery period: **2026-01-02 00:00 UTC to 2026-02-01 23:30 UTC** (31 delivery days = 1,488 settlement periods, 100.0% coverage).
3. **Data Scope & Offline Bundling:**
   - Both `FUELHH` actuals and `WINDFOR` forecasts are pre-fetched from Elexon BMRS API and stored locally as clean CSV files in `backend/data/`.
   - The running application operates completely offline with zero runtime external API dependencies.
4. **Single Source of Truth:**
   - The FastAPI backend computes all metrics, percentiles (nearest-rank P50, P90, P99), 500 MW histogram bins, and horizon lead-time progressions. The React frontend contains zero arithmetic recalculation logic and performs presentation formatting only.

---

## Files and Directories

```text
Gridbricks/
├── .env.example                                      # Environment variable template
├── .gitignore                                        # Root Git ignore rules (caches, node_modules)
├── README.md                                         # Project documentation & operational guide
├── requirements.txt                                  # Root Python dependencies for Vercel deployment
├── docker-compose.yml                                # Multi-container production deployment config
├── vercel.json                                       # Vercel serverless deployment routing
├── api/
│   └── index.py                                      # Vercel serverless ASGI gateway to FastAPI
├── backend/
│   ├── Dockerfile                                    # FastAPI container configuration (TZ=UTC)
│   ├── __init__.py                                   # Python module initialization
│   ├── data_loader.py                                # CSV data ingestion and in-memory cache
│   ├── forecast_engine.py                            # Pure-function quantitative calculation engine
│   ├── main.py                                       # FastAPI REST endpoints & CORS configuration
│   ├── requirements.txt                              # Backend Python dependencies
│   ├── data/
│   │   ├── actuals.csv                               # Metered wind generation actuals (FUELHH)
│   │   └── forecasts.csv                             # National wind forecasts (WINDFOR)
│   └── tests/
│       ├── test_api.py                               # FastAPI endpoint status & schema tests
│       ├── test_forecast_engine.py                   # Engine logic, cutoff & histogram unit tests
│       └── test_reconciliation.py                   # UTC epoch & daily reconciliation proofs
├── docs/
│   ├── FINDINGS.md                                   # Empirical findings & segregated hypotheses
│   └── daily_table.csv                               # Canonical 31-day daily metrics breakdown
├── frontend/
│   ├── Dockerfile                                    # Multi-stage Nginx container build (TZ=UTC)
│   ├── index.html                                    # Main HTML document entrypoint
│   ├── nginx.conf                                    # Nginx reverse proxy configuration (port 80)
│   ├── package.json                                  # Frontend NPM packages and scripts
│   ├── package-lock.json                             # Exact frontend dependency tree lockfile
│   ├── tsconfig.json                                 # TypeScript compiler options
│   ├── vite.config.ts                                # Vite development and bundling configuration
│   ├── public/
│   │   └── favicon.svg                               # Wind turbine SVG brand icon
│   └── src/
│       ├── App.jsx                                   # Top-level React dashboard application
│       ├── api.js                                    # API client communicating with backend
│       ├── index.css                                 # Design system tokens and Tailwind CSS rules
│       ├── main.tsx                                  # React DOM bootstrap entry
│       ├── vite-env.d.ts                             # Vite environment TypeScript definitions
│       ├── components/
│       │   ├── Controls.jsx                          # Horizon & date selection controls
│       │   ├── Footer.jsx                            # Operational methodology and Elexon citations
│       │   ├── Header.jsx                            # Application header with UTC status clocks
│       │   ├── Hero.jsx                              # 31-day thumbnail strip & focus day metrics
│       │   ├── MainChart.jsx                         # Recharts time-series chart with actuals vs forecasts
│       │   ├── Metrics.jsx                           # KPI summary cards (MAE, Bias, RMSE, MAPE)
│       │   ├── States.jsx                            # Loading and error state presentation
│       │   ├── SupportCharts.jsx                     # 500 MW histogram & horizon lead-time curves
│       │   └── WindField.jsx                         # Ambient particle animation backdrop
│       └── lib/
│           ├── analysis.js                           # UI display constants and labels
│           └── format.js                             # Number and date formatting utilities
└── scripts/
    ├── fetch_data.py                                 # Pipeline to fetch and update Elexon CSV datasets
    └── independent_pandas_validation.py              # Standalone pandas script verifying 40 samples
```

---

## How to Run

### Option 1: Running with Docker (Recommended)

1. **Start the multi-container stack:**
   ```bash
   docker compose up --build
   ```

2. **Access the application:**
   - **Web Dashboard:** [http://localhost:3000](http://localhost:3000)
   - **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### Option 2: Running Locally without Docker

#### 1. Backend Setup:
```bash
# From workspace root:
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Backend API will be live at `http://127.0.0.1:8000`.

#### 2. Frontend Setup (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```
Frontend development server will open at `http://localhost:5173`.

---

### Option 3: Running Automated Tests

Run the full pytest suite (25 unit and integration tests):
```bash
python -m pytest backend/tests/ -v
```

All 25 tests execute in under 2 seconds, verifying:
- FastAPI endpoints (inclusive date filtering, 2 days = 96 rows).
- Cutoff boundary enforcement and horizon filtering.
- UTC epoch millisecond alignment (`t == epoch_ms(startTime)` and `publish == epoch_ms(publishTime)`).
- Exact mathematical reconciliation between daily rows and monthly totals ($0.000000\text{ MW}$ delta).
- 20-bin contiguous 500 MW histogram without gaps, exactly summing to 1,488 settlement periods.
