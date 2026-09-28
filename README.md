# Retail Analytics Command Center

A Streamlit analytics and forecasting platform built on the UCI Online Retail dataset.
Modules: Sales Analytics, Sales Forecast (SARIMA), Stratified Sampling, DSE Stock Predictor, Portfolio Gallery.

**Principle:** analysis logic lives in `src/` (no Streamlit code, testable). `views/` only draws the UI.

---

## Project structure

```text
app.py                     entry point + navigation
requirements.txt
data/raw/                  original dataset, never edited
data/processed/            generated clean dataset + cleaning report
src/
  config.py                paths, column names, constants
  data_loader.py           read raw file, validate schema, load processed
  preprocessing.py         clean + feature engineering
  analytics.py             KPIs and aggregations
  forecasting.py           weekly series, baseline, SARIMA, metrics
  sampling.py              stratified sampling logic
  stock_prediction.py      DSE features + model
views/                     one file per Streamlit page
scripts/build_dataset.py   raw -> processed
tests/                     pytest
models/  assets/screenshots/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Put the UCI Online Retail file in `data/raw/` as `online_retail.csv`.
Source: https://archive.ics.uci.edu/dataset/352/online+retail

Run the app: `streamlit run app.py`  |  Run tests: `pytest`

---

## Build roadmap (tick as you go)

Deploy after Step 0 and push after every step. Streamlit Community Cloud redeploys on each push.

### Step 0: Live shell
- [ ] Put a `st.title(...)` in `app.py`, run locally
- [ ] Push to GitHub
- [ ] share.streamlit.io: New app, repo, branch `main`, file `app.py`
- [ ] Public URL works

### Step 1: `src/config.py`
- [ ] `ROOT`, `RAW_DIR`, `PROCESSED_DIR` using `pathlib`
- [ ] Required columns: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country
- [ ] Cancellation prefix `"C"`, non-product codes (POST, D, M, BANK CHARGES, ...)
- Check: `python -c "from src import config; print(config.ROOT)"`

### Step 2: `src/data_loader.py` and `src/preprocessing.py`
- [ ] `load_raw()`: read CSV, IDs as strings
- [ ] `validate_schema()`: clear error if columns are missing
- [ ] `clean()`: convert dates/numbers, drop duplicates, cancellations, quantity <= 0, price <= 0, non-product codes
- [ ] Keep rows with missing CustomerID (real revenue), add a `HasCustomer` flag
- [ ] Features: `Revenue = Quantity * UnitPrice`, Date, Year, Month, YearMonth, Week
- [ ] Return a cleaning report (rows removed per step) for the methodology section
- [ ] Never modify the raw file
- Check: row counts add up; write `tests/test_preprocessing.py` with a tiny fake DataFrame

### Step 3: `scripts/build_dataset.py` and data for deploy
- [ ] raw -> clean -> save `data/processed/retail_clean.parquet` + `cleaning_report.json`
- [ ] Remove the `data/processed/*` lines from `.gitignore` so the parquet is committed (about 10 MB)
- [ ] Push, so the cloud app has data

### Step 4: `views/overview.py`
- [ ] Load parquet with `@st.cache_data`
- [ ] KPI cards: revenue, orders, units, customers, AOV, countries (calculated, never hardcoded)
- [ ] Show the cleaning report table
- Live check: correct numbers on your public URL

### Step 5: Sales Analytics (`src/analytics.py` + `views/sales_analytics.py`)
- [ ] Filters: country, product, year, month, applied once to one filtered DataFrame
- [ ] Monthly revenue line chart (Plotly)
- [ ] Orders by month bar chart
- [ ] Top 5/10/20 products (horizontal bar)
- [ ] Country revenue chart
- [ ] Transaction table + `st.download_button` (CSV)
- Rule: calculations in `analytics.py`, pages only draw

### Step 6: Sales Forecast (`src/forecasting.py` + page)
- [ ] Weekly revenue series
- [ ] Trend, seasonality, stationarity (ADF), ACF/PACF plots
- [ ] Baseline: seasonal naive
- [ ] SARIMA (statsmodels), 12-week forecast with confidence band
- [ ] Train/test split, MAE / RMSE / MAPE, actual vs predicted
- [ ] Experiment table: Seasonal Naive vs SARIMA
- [ ] Methodology and limitations section

### Step 7: Stratified Sampling (`src/sampling.py` + page)
- [ ] Upload dataset, choose stratification variable and sample size
- [ ] Allocation: proportional, equal, Neyman
- [ ] Population vs sample distribution charts, download sample

### Step 8: DSE Stock Predictor (`src/stock_prediction.py` + page)
- [ ] Features: returns, moving average, rolling volatility, RSI
- [ ] Logistic Regression for next-period UP/DOWN
- [ ] Time-based split (never shuffle), evaluation metrics

### Step 9: Gallery, docs, polish
- [ ] Gallery cards with screenshots (`assets/screenshots/`)
- [ ] Screenshots in this README, final deploy

---

## Later (parked)
Supabase as data store, with Make.com and CSV upload for ingestion. Keep `data_loader.py` behind a `data_source` switch so pages never change.

## Notes
- Dataset: UCI Online Retail, CC BY 4.0. Credit the source in the app.
- Pin package versions in `requirements.txt` before deploying.
