# Empirical Findings & Forecast Audit Report: UK Wind Generation (January 2026)

This document provides a factual, empirical evaluation of Elexon BMRS actual wind generation (`FUELHH`, `fuelType='WIND'`) and day-ahead / horizon wind forecasts (`WINDFOR`) for delivery days in January 2026.

All figures in Sections 1 and 2 are calculated directly from the underlying datasets. Speculative or unverified domain explanations are explicitly separated into Section 3 as **untested hypotheses**.

---

## 1. Confirmed Empirical Facts from the Data

### 1.1 Dataset Scope and Totals
- **Delivery Period**: January 1, 2026, 00:00 UTC to January 31, 2026, 23:30 UTC.
- **Total Settlement Periods**: 1,488 half-hours (31 days × 48 half-hours).
- **Matched Coverage**: Exactly 1,488 / 1,488 periods (100.0% coverage).
- **Overall Day-Ahead Metrics** (Decision Cutoff: Day $D-1$ at 09:00 UTC):
  - Mean Actual Generation: **11,580.7 MW**
  - Mean Forecast Generation: **13,432.6 MW**
  - Overall Mean Bias ($\text{Forecast} - \text{Actual}$): **+1,851.9 MW**
  - Mean Absolute Error (MAE): **2,145.2 MW**
  - Root Mean Squared Error (RMSE): **2,615.8 MW**
  - P50 Absolute Error: **1,795.5 MW**
  - P90 Absolute Error: **4,274.9 MW**
  - P99 Absolute Error: **6,359.9 MW**
  - Zero-Safe MAPE: **22.44%**

---

### 1.2 All 31 Days Daily Breakdown & Concentration Analysis

| Date | Periods | Avg Actual (MW) | Max Actual (MW) | Avg Forecast (MW) | Mean Bias (MW) | Daily MAE (MW) | Share of Monthly Bias |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-01-01** | 48 | 15,372.0 MW | 16,408.0 MW | 19,579.5 MW | +4,207.5 MW | 4,207.5 MW | **+7.33%** |
| **2026-01-02** | 48 | 15,169.1 MW | 16,125.0 MW | 18,279.0 MW | +3,109.9 MW | 3,109.9 MW | **+5.42%** |
| **2026-01-03** | 48 | 15,251.2 MW | 16,012.0 MW | 17,294.0 MW | +2,042.8 MW | 2,042.8 MW | +3.56% |
| **2026-01-04** | 48 | 13,343.2 MW | 15,016.0 MW | 15,252.0 MW | +1,908.8 MW | 1,908.8 MW | +3.32% |
| **2026-01-05** | 48 | 9,439.4 MW | 10,869.0 MW | 11,816.5 MW | +2,377.1 MW | 2,377.1 MW | +4.14% |
| **2026-01-06** | 48 | 9,448.5 MW | 16,757.0 MW | 11,833.0 MW | +2,384.5 MW | 2,512.4 MW | +4.15% |
| **2026-01-07** | 48 | 12,143.1 MW | 15,211.0 MW | 13,611.2 MW | +1,468.1 MW | 1,498.9 MW | +2.56% |
| **2026-01-08** | 48 | 4,528.1 MW | 10,700.0 MW | 5,372.8 MW | +844.8 MW | 1,949.2 MW | +1.47% |
| **2026-01-09** | 48 | 10,756.9 MW | 12,045.0 MW | 11,561.8 MW | +804.9 MW | 850.6 MW | +1.40% |
| **2026-01-10** | 48 | 8,779.2 MW | 11,309.0 MW | 8,693.1 MW | **-86.1 MW** | 1,103.2 MW | **-0.15%** |
| **2026-01-11** | 48 | 13,557.4 MW | 16,018.0 MW | 18,359.0 MW | +4,801.6 MW | 4,801.6 MW | **+8.36%** |
| **2026-01-12** | 48 | 14,452.2 MW | 15,468.0 MW | 19,320.5 MW | +4,868.2 MW | 4,868.2 MW | **+8.48%** |
| **2026-01-13** | 48 | 10,068.5 MW | 13,266.0 MW | 10,225.0 MW | +156.5 MW | 1,420.3 MW | +0.27% |
| **2026-01-14** | 48 | 9,670.6 MW | 14,482.0 MW | 9,586.5 MW | **-84.2 MW** | 1,088.3 MW | **-0.15%** |
| **2026-01-15** | 48 | 10,567.8 MW | 14,602.0 MW | 11,609.6 MW | +1,041.8 MW | 1,041.8 MW | +1.81% |
| **2026-01-16** | 48 | 7,578.5 MW | 9,284.0 MW | 7,930.4 MW | +352.0 MW | 800.5 MW | +0.61% |
| **2026-01-17** | 48 | 5,647.0 MW | 8,999.0 MW | 7,373.8 MW | +1,726.8 MW | 1,726.8 MW | +3.01% |
| **2026-01-18** | 48 | 4,977.0 MW | 6,834.0 MW | 6,531.8 MW | +1,554.8 MW | 1,554.8 MW | +2.71% |
| **2026-01-19** | 48 | 6,526.1 MW | 11,670.0 MW | 5,796.0 MW | **-730.1 MW** | 742.9 MW | **-1.27%** |
| **2026-01-20** | 48 | 15,130.2 MW | 16,995.0 MW | 15,482.1 MW | +351.8 MW | 1,058.5 MW | +0.61% |
| **2026-01-21** | 48 | 15,731.7 MW | 17,606.0 MW | 19,390.0 MW | +3,658.3 MW | 3,658.3 MW | **+6.37%** |
| **2026-01-22** | 48 | 16,188.6 MW | 17,587.0 MW | 18,855.0 MW | +2,666.4 MW | 2,666.4 MW | **+4.64%** |
| **2026-01-23** | 48 | 16,146.4 MW | 17,578.0 MW | 17,661.2 MW | +1,514.8 MW | 1,514.8 MW | +2.64% |
| **2026-01-24** | 48 | 15,867.2 MW | 17,805.0 MW | 17,793.1 MW | +1,925.9 MW | 1,925.9 MW | +3.35% |
| **2026-01-25** | 48 | 13,602.2 MW | 17,114.0 MW | 15,493.5 MW | +1,891.2 MW | 1,891.2 MW | +3.29% |
| **2026-01-26** | 48 | 10,439.9 MW | 16,626.0 MW | 12,420.8 MW | +1,980.9 MW | 1,980.9 MW | +3.45% |
| **2026-01-27** | 48 | 16,408.5 MW | 17,593.0 MW | 19,887.6 MW | +3,479.1 MW | 3,479.1 MW | **+6.06%** |
| **2026-01-28** | 48 | 5,759.8 MW | 10,825.0 MW | 11,134.6 MW | +5,374.8 MW | 5,374.8 MW | **+9.36%** |
| **2026-01-29** | 48 | 10,192.5 MW | 13,512.0 MW | 11,931.5 MW | +1,739.0 MW | 1,739.0 MW | +3.03% |
| **2026-01-30** | 48 | 15,837.1 MW | 16,865.0 MW | 17,208.8 MW | +1,371.7 MW | 1,378.9 MW | +2.39% |
| **2026-01-31** | 48 | 10,423.2 MW | 15,657.0 MW | 12,813.3 MW | +2,390.2 MW | 2,390.2 MW | +4.16% |

#### Bias Concentration:
- **Top 5 Days by signed over-forecast error**:
  1. `2026-01-28`: +5,374.8 MW (9.36%)
  2. `2026-01-12`: +4,868.2 MW (8.48%)
  3. `2026-01-11`: +4,801.6 MW (8.36%)
  4. `2026-01-01`: +4,207.5 MW (7.33%)
  5. `2026-01-21`: +3,658.3 MW (6.37%)
  - **Combined Top 5 Days Contribution**: **39.91%** of total monthly signed error.
- **Top 8 Days** (adding Jan 27, Jan 02, Jan 22):
  - **Combined Top 8 Days Contribution**: **56.03%** of total monthly signed error.
- Days with negative bias (under-forecasting): Jan 10 (-86.1 MW), Jan 14 (-84.2 MW), Jan 19 (-730.1 MW).

---

### 1.3 Bias and MAE Binned by Forecast Generation Level

| Forecast Bin (MW) | Periods | % of Periods | Mean Forecast (MW) | Mean Actual (MW) | Mean Bias (MW) | MAE (MW) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0 to 5,000 MW** | 60 | 4.0% | 4,317.4 MW | 3,750.2 MW | **+567.2 MW** | 1,285.0 MW |
| **5,000 to 10,000 MW** | 384 | 25.8% | 7,932.2 MW | 7,190.1 MW | **+742.0 MW** | 1,597.5 MW |
| **10,000 to 15,000 MW** | 400 | 26.9% | 12,355.3 MW | 10,766.9 MW | **+1,588.5 MW** | 1,698.0 MW |
| **15,000 to 20,000 MW** | 554 | 37.2% | 17,863.5 MW | 15,352.4 MW | **+2,511.1 MW** | 2,548.9 MW |
| **20,000+ MW** | 90 | 6.0% | 20,491.8 MW | 15,934.6 MW | **+4,557.2 MW** | **4,557.2 MW** |

**Empirical Observations from Binning**:
1. Bias scales strictly monotonically with the forecast generation level, rising from `+567.2 MW` when forecast $< 5\text{ GW}$ to `+4,557.2 MW` when forecast $> 20\text{ GW}$.
2. In the `20,000+ MW` bin, $\text{MAE} = \text{Bias} = 4,557.2\text{ MW}$, meaning 100% of periods in this bin were over-forecasts ($\text{Forecast} > \text{Actual}$ in every single half-hour).
3. The highest half-hourly actual wind generation recorded anywhere in January 2026 was **17,805.0 MW** (on 2026-01-24 at 18:00 UTC). Forecasts above 17,805 MW consistently exceeded actual outturn.

---

### 1.4 Horizon Error Progression Curve (0h to 48h, Every 3 Hours)

| Horizon (Hours) | Evaluated Periods | Coverage | MAE (MW) | RMSE (MW) | Mean Bias (MW) | P90 Abs Error (MW) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0 h** | 1,488 | 100.0% | 1,804.2 MW | 2,291.8 MW | +1,592.9 MW | 3,783.9 MW |
| **3 h** | 1,488 | 100.0% | 1,842.2 MW | 2,336.7 MW | +1,627.5 MW | 3,889.0 MW |
| **6 h** | 1,488 | 100.0% | 1,884.9 MW | 2,362.0 MW | +1,683.6 MW | 3,892.5 MW |
| **9 h** | 1,488 | 100.0% | 1,899.5 MW | 2,374.5 MW | +1,691.0 MW | 3,943.1 MW |
| **12 h** | 1,488 | 100.0% | 1,911.4 MW | 2,389.0 MW | +1,704.4 MW | 3,950.4 MW |
| **15 h** | 1,488 | 100.0% | 1,953.4 MW | 2,425.1 MW | +1,746.5 MW | 3,951.8 MW |
| **18 h** | 1,488 | 100.0% | 1,995.2 MW | 2,463.5 MW | +1,791.2 MW | 3,951.3 MW |
| **21 h** | 1,488 | 100.0% | 2,031.9 MW | 2,487.4 MW | +1,818.4 MW | 3,968.5 MW |
| **24 h** | 1,488 | 100.0% | 2,066.8 MW | 2,528.5 MW | +1,854.6 MW | 4,134.2 MW |
| **27 h** | 1,488 | 100.0% | 2,117.5 MW | 2,584.7 MW | +1,876.2 MW | 4,256.4 MW |
| **30 h** | 1,488 | 100.0% | 2,205.0 MW | 2,659.2 MW | +1,897.5 MW | 4,352.2 MW |
| **33 h** | 1,488 | 100.0% | 2,248.1 MW | 2,715.5 MW | +1,925.5 MW | 4,346.0 MW |
| **36 h** | 1,488 | 100.0% | 2,273.0 MW | 2,761.5 MW | +1,951.1 MW | 4,308.1 MW |
| **39 h** | 1,488 | 100.0% | 2,304.9 MW | 2,809.3 MW | +1,959.4 MW | 4,447.1 MW |
| **42 h** | 1,488 | 100.0% | 2,324.0 MW | 2,851.0 MW | +1,939.7 MW | 4,472.3 MW |
| **45 h** | 1,364 | 91.7% | 2,388.8 MW | 2,920.9 MW | +1,944.3 MW | 4,584.5 MW |
| **48 h** | 1,178 | 79.2% | 2,389.0 MW | 2,943.1 MW | +1,867.8 MW | 4,746.1 MW |

---

## 2. December 2025 Comparative Baseline

Evaluated across the 528 half-hours from December 21, 2025, 00:00 UTC to December 31, 2025, 23:30 UTC:
- **Mean Actual Generation**: 9,148.9 MW
- **Mean Forecast Generation**: 8,952.0 MW
- **Mean Bias**: **-196.9 MW** (slight under-forecast)
- **MAE**: **1,045.9 MW**
- **RMSE**: **1,400.2 MW**
- **P90 Absolute Error**: **2,398.2 MW**

*Fact*: In the available late December 2025 sample, there was no systematic positive bias.

---

## 3. Untested Hypotheses (Requiring External Verification)

The following claims are **hypotheses only** and are not verified by Elexon BMRS `FUELHH` and `WINDFOR` datasets alone:

1. **Turbine High-Wind Cut-out Hypothesis**:
   - *Hypothesis*: Physical wind turbine blades may have automatically feathered/shut down due to wind speeds exceeding threshold limits ($>25\text{ m/s}$), causing actual generation to fall below meteorological forecasts.
   - *Status*: **Untested**. Validating this requires anemometer wind speed observations and individual turbine SCADA status data, which are not present in Elexon BMRS.
2. **Transmission Boundary Curtailment Hypothesis**:
   - *Hypothesis*: Grid constraints (such as the B6 Anglo-Scottish boundary) may have prompted the ESO to issue Bid-Offer Acceptances (BOAs) curtailing wind farms in the Balancing Mechanism, suppressing metered `FUELHH` output.
   - *Status*: **Untested**. Validating this requires cross-referencing Balancing Mechanism BOA acceptance volumes (`BOALF` dataset).
3. **Severe Weather Front Dates Hypothesis**:
   - *Hypothesis*: Peaks in error on specific dates (e.g., Jan 1–2, 11–12, 27–28) coincided with named meteorological storm depressions.
   - *Status*: **Untested**. Validating this requires official UK Met Office meteorological synoptic charts.
4. **NWP Hindcast Assimilation Window Hypothesis**:
   - *Hypothesis*: Records in `WINDFOR` where $\text{startTime} < \text{publishTime}$ represent numerical weather prediction model re-initialization assimilation cycles.
   - *Status*: **Untested**. Validating this requires model technical documentation from the forecasting provider / Met Office.
