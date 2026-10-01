# Sales Forecasting — Methodology, Results, Limitations

Working notes for `src/forecasting.py` (Step 6). Source for the research paper's
methodology and limitations sections. Numbers below were regenerated directly
from `data/processed/retail_clean.parquet` on 2026-09-29; re-run the snippets
in this file if the processed dataset changes.

## 1. Data preparation

- **Series:** daily total `Revenue`, built by `aggregate_daily()` — group the
  cleaned transaction table by `Date`, sum `Revenue`, then reindex against a
  full calendar range so every day exists (missing days become `0`, not a gap).
- **Range:** 374 consecutive days, 2010-12-01 to 2011-12-09. No missing values
  after reindexing.
- **Zero-revenue days:** 69 of 374 (18.4%). Breakdown by weekday:

  | Weekday | Count |
  |---|---|
  | Saturday | 53 |
  | Monday | 6 |
  | Friday | 4 |
  | Sunday | 3 |
  | Tue / Wed / Thu | 1 each |

  Saturdays are structurally non-trading days for this dataset (77% of all
  zero days). The remaining 16 zero days fall on other weekdays and are most
  likely UK public holidays (Christmas, New Year, etc.), not missing data —
  worth stating explicitly rather than attributing all zero days to Saturday
  alone.

## 2. Train/test split

- `train_test_split_series(daily, test_days=28)` — chronological split, no
  shuffling, no overlap.
- Train: 346 days, ending 2011-11-11.
- Test: 28 days, 2011-11-12 to 2011-12-09.

## 3. Stationarity and seasonality

- **ADF test** (`check_stationarity`, on `train`): statistic = -2.460,
  p = 0.126 → **not stationary** at the 5% level. This motivates first-order
  differencing (`d=1`) in the SARIMA order below.
- **ACF/PACF** (computed interactively, `plot_acf`/`plot_pacf`, 21 lags):
  autocorrelation pattern repeats at lag 7 → **weekly seasonality**, `s = 7`.

## 4. Baseline: seasonal naive

`seasonal_naive_forecast(train, test, season=7)` predicts each test day as the
actual value from 7 days earlier (spanning the train/test boundary correctly).

| Metric | Value |
|---|---|
| MAE | 15,462.72 |
| RMSE | 31,609.09 |
| MAPE | 25.29% |
| WAPE | 28.82% |
| MASE | 1.466 |

## 5. SARIMA model selection

Three candidates fit with `fit_sarima(train, order, seasonal_order)`,
evaluated on the same 28-day test window:

| Model | AIC | BIC | MAE | RMSE | MAPE | WAPE | MASE |
|---|---|---|---|---|---|---|---|
| SARIMA(1,1,0)(1,1,0,7) | 7527.58 | 7539.05 | 17,348.93 | 29,813.78 | 32.84% | 32.33% | 1.645 |
| **SARIMA(1,1,1)(1,1,1,7)** (chosen) | 7406.00 | 7425.12 | 15,743.25 | 31,450.53 | 20.49% | 29.34% | 1.493 |
| SARIMA(2,1,1)(1,1,1,7) | 7403.49 | 7426.43 | 15,812.46 | 31,664.58 | 20.50% | 29.47% | 1.499 |

**Chosen model: SARIMA(1,1,1)(1,1,1,7).** The (2,1,1) variant has a marginally
lower AIC but a *higher* BIC (which penalizes the extra parameter more) and no
practical improvement on any test-set metric — so the simpler (1,1,1) model
was preferred on parsimony grounds. (1,1,0) is clearly worse on every metric
and was rejected outright.

`forecast_with_ci(model, steps, alpha=0.05)` produces the 12-week-ahead point
forecast with a 95% confidence band for the live app.

## 6. Result: metrics disagree on which model wins — and why

Baseline (naive) vs. chosen SARIMA, same test set:

| Metric | Naive | SARIMA | Winner |
|---|---|---|---|
| MAE | 15,462.72 | 15,743.25 | Naive |
| RMSE | 31,609.09 | 31,450.53 | ~tie (SARIMA, marginal) |
| MAPE | 25.29% | 20.49% | SARIMA |
| WAPE | 28.82% | 29.34% | Naive |
| MASE | 1.466 | 1.493 | Naive |

**This is a real, reproducible finding, not a computation error** (verified
by direct comparison on identical actual/predicted series). The disagreement
comes from how each metric weights errors:

- **MAPE** averages *percentage* errors per day, so a small £ miss on a
  low-revenue day counts as a large % error, while a large £ miss on a
  high-revenue day barely moves the average. This makes MAPE most sensitive
  to accuracy on *ordinary* days.
- **MAE / RMSE / WAPE / MASE** weight everything in raw £, so they are
  dominated by the highest-revenue days. The single worst day in the test
  window is **2011-12-09** (the last test day): actual revenue £198,095 vs.
  a SARIMA prediction of £51,865 (73.8% off). That one day alone accounts
  for **33.2% of SARIMA's total absolute error** across the 28-day test
  set. Naive also misses this day badly (£142,178 error) but by less than
  SARIMA (£146,230) — enough on its own to flip MAE/WAPE/MASE in naive's
  favor despite SARIMA being more accurate on ordinary days.

  (Correction: an earlier version of this note described this as "a
  ~£1.4M single-day spike in November" — that £1.4M figure was the
  *monthly* total from the Monthly Revenue chart, misread as a single
  day's revenue. The actual daily figure, verified directly from the
  error breakdown, is £198,095 on 2011-12-09.)

**Why this actually happens (verified, 2026-10-02):** checked the raw
transactions for 2011-12-09 directly. One customer (ID 16446) placed a
single order (invoice 581483) worth £168,470 — 85.0% of that day's entire
revenue, across 35 customers trading that day. This same customer placed
only one other order in the whole dataset: £2.90, back in May. It's a
one-off customer-level demand shock, not a seasonal or calendar pattern —
nothing in the aggregate daily revenue series gives a model any signal
that this was coming, because there isn't one.

(Correction #2: an earlier version of this note attributed this to "the
start of the pre-Christmas shopping period" — a calendar hypothesis that
sounded plausible but wasn't checked against the actual transactions. It's
now been checked, and superseded by the finding above.)

**Conclusion for the paper:** SARIMA(1,1,1)(1,1,1,7) improves relative (%)
accuracy over the seasonal-naive baseline but not absolute (£) accuracy,
due to one unforecastable customer-level order that dominates the test
window's £-weighted error. This isn't a modeling flaw to fix with better
tuning or more features — it's a single transaction outside what any
aggregate-revenue time-series model could see coming. Report multiple
metrics rather than one; a single metric here would misrepresent the
model's behavior in either direction.

## 7. Limitations

- **MAPE is undefined at zero actuals.** `evaluate_forecast` excludes days
  where `actual == 0` (mostly Saturdays, see §1) from the MAPE calculation —
  those days are silently dropped from that metric, not penalized. WAPE and
  MASE do not have this problem (aggregate-then-divide, and scale-based,
  respectively) and are reported alongside MAPE for this reason.
- **MASE reference point.** The naive-forecast MASE itself is 1.466, not
  exactly 1.0 — MASE's denominator is the naive method's *in-sample*
  (training-set) error, while the numerator is evaluated on the *test* period,
  so even the naive method's own test-set MASE need not equal 1 exactly.
- **Single train/test split.** One chronological 346/28 split, not
  cross-validated (e.g. rolling-origin backtesting) — the reported metrics
  reflect performance over one specific 28-day window, which happens to
  include one unusually large one-off customer order (see §6) and may not
  generalize to other periods.
- **Model search scope.** `tune_sarima()` grid-searched 144 (order,
  seasonal_order) combinations (p,q ∈ {0,1,2}, d ∈ {0,1}, P,D,Q ∈ {0,1},
  s=7 fixed), all scored on the one 28-day test window — confirmed
  SARIMA(1,1,1)(1,1,1,7) as MAPE-optimal (20.485%, vs. runner-up
  SARIMA(2,1,1)(1,1,1,7) at 20.496%). Not explored: p/q > 2, other values
  of s, or cross-validated scoring across multiple windows.
- **Deploy dependency risk (fixed):** `forecasting.py` originally imported
  `matplotlib` unconditionally at module level for ACF/PACF plotting, but
  `matplotlib` was never in `requirements.txt`. That import would have failed
  on Streamlit Community Cloud the moment any page imported this module. The
  import has been removed (ACF/PACF was exploratory only); the app's charts
  use Plotly exclusively per the project's own convention.
