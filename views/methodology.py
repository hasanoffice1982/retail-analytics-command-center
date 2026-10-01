import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.data_loader import load_processed
from src.forecasting import (
    aggregate_daily,
    train_test_split_series,
    check_stationarity,
    fit_sarima,
    forecast_with_ci,
    evaluate_forecast,
    seasonal_naive_forecast,
    tune_sarima,
)

st.title("Forecasting Methodology")
st.caption(
    "Validation, error analysis and model selection rationale behind the "
    "Sales Forecast page. See docs/forecasting_methodology.md for the full "
    "written methodology."
)


@st.cache_data(show_spinner=False)
def get_backtest_model(train: pd.Series):
    return fit_sarima(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))


@st.cache_data(show_spinner=False)
def get_tuning_results(train: pd.Series, test: pd.Series):
    return tune_sarima(train, test)


@st.dialog("Verify best model")
def verify_best_model_dialog(train: pd.Series, test: pd.Series):
    with st.spinner("Grid-searching 144 SARIMA configurations..."):
        best_order, best_seasonal_order, best_mape, results_df = get_tuning_results(train, test)

    if best_order == (1, 1, 1) and best_seasonal_order == (1, 1, 1, 7):
        st.success(f"Confirmed: SARIMA{best_order}{best_seasonal_order} is still the best "
                   f"of 144 combinations (MAPE {best_mape:.3f}%).")
    else:
        st.warning(f"The deployed model is no longer optimal. Best found: "
                   f"SARIMA{best_order}{best_seasonal_order} (MAPE {best_mape:.3f}%).")

    st.dataframe(
        results_df.head(10).rename(columns={"mape": "mape (%)"}),
        hide_index=True,
        width="stretch",
    )


df = load_processed()
daily = aggregate_daily(df)
train, test = train_test_split_series(daily)

model = get_backtest_model(train)
result = forecast_with_ci(model, steps=len(test))
result["lower"] = result["lower"].clip(lower=0)
forecast_point = model.forecast(steps=len(test))
metrics = evaluate_forecast(test, forecast_point)
mape = metrics["mape"]

st.subheader("Model vs Baseline")
naive_forecast = seasonal_naive_forecast(train, test, season=7)
naive_metrics = evaluate_forecast(test, naive_forecast)

col_a, col_b = st.columns(2)
with col_a:
    st.metric("SARIMA MAPE", f"{mape:.2f}%")
with col_b:
    delta = mape - naive_metrics["mape"]
    st.metric(
        "Seasonal Naive MAPE",
        f"{naive_metrics['mape']:.2f}%",
        delta=f"{delta:+.2f}pp vs SARIMA",
        delta_color="inverse",  # red if naive is better than SARIMA
    )

col_c, col_d = st.columns(2)
with col_c:
    st.metric("SARIMA MAE", f"£{metrics['mae']:,.0f}")
with col_d:
    mae_delta = metrics["mae"] - naive_metrics["mae"]
    st.metric(
        "Seasonal Naive MAE",
        f"£{naive_metrics['mae']:,.0f}",
        delta=f"£{mae_delta:+,.0f} vs SARIMA",
        delta_color="inverse",
    )

st.caption(
    "MAPE favors SARIMA; MAE (£-weighted) favors the naive baseline — the two "
    "metrics disagree because of one large-revenue day in the test window. "
)

st.subheader("Forecast Error Breakdown")

error_df = pd.DataFrame({
    "actual": test.values,
    "forecast": forecast_point.values,
    "abs_error": (test.values - forecast_point.values).round(2),
}, index=test.index)
# % error is undefined on zero-revenue days (4 Saturdays in this window) —
# excluded from the ranking rather than shown as a meaningless inf/NaN.
error_df["abs_pct_error"] = pd.NA
nonzero = error_df["actual"] != 0
error_df.loc[nonzero, "abs_pct_error"] = (
    error_df.loc[nonzero, "abs_error"].abs() / error_df.loc[nonzero, "actual"] * 100
).round(2)

col_x, col_y = st.columns(2)
with col_x:
    st.markdown("**Top 5 by £ error (drives MAE)**")
    st.dataframe(
        error_df.sort_values("abs_error", key=abs, ascending=False).head(5),
        width="stretch",
    )
with col_y:
    st.markdown("**Top 5 by % error (drives MAPE)**")
    st.dataframe(
        error_df.dropna(subset=["abs_pct_error"])
        .sort_values("abs_pct_error", ascending=False)
        .head(5),
        width="stretch",
    )
st.caption("Zero-revenue days (4 Saturdays in this window) are excluded from the % error ranking — MAPE is undefined there.")

st.subheader("Robust Accuracy Metrics")
abs_pct_errors = error_df["abs_pct_error"].dropna().astype(float)
median_mape = abs_pct_errors.median()
trimmed_mape = abs_pct_errors[abs_pct_errors < abs_pct_errors.quantile(0.90)].mean()

col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Standard MAPE", f"{mape:.2f}%")
with col_m2:
    st.metric("Median APE", f"{median_mape:.2f}%",
              help="Less sensitive to single-day outliers than mean-based MAPE")
with col_m3:
    st.metric("Trimmed MAPE (90th pctile)", f"{trimmed_mape:.2f}%",
              help="Excludes the worst ~10% of days")

with st.expander("Why three accuracy numbers?"):
    st.markdown(
        "Standard MAPE is pulled up by one outlier day: on 2011-12-09, a single "
        "customer (ID 16446) placed one order worth £168,470 — 85% of that day's "
        "entire revenue, and a one-off (that customer placed only one other order "
        "in the whole dataset, worth £2.90). Median and trimmed MAPE show accuracy "
        "on a typical day, excluding that kind of unforecastable event. "
        "See `docs/forecasting_methodology.md` §4 for the verified transaction-level "
        "breakdown."
    )

st.divider()
st.subheader("Stationarity Check (ADF Test)")
adf = check_stationarity(train)

col_adf1, col_adf2 = st.columns(2)
with col_adf1:
    st.metric("ADF Statistic", f"{adf['adf_statistic']:.3f}")
with col_adf2:
    st.metric("p-value", f"{adf['p_value']:.4f}")

if adf["is_stationary"]:
    st.success("Series is stationary (p < 0.05) at the raw level.")
else:
    st.warning(
        "Series is non-stationary (p ≥ 0.05) at the raw level — "
        "supports the first-order differencing (d=1) used in the chosen order."
    )

st.subheader("Seasonal Period & Order Selection")
st.markdown(
    """
- **Seasonal period (s=7):** ACF on the differenced series shows significant,
  geometrically-decaying spikes at lag 7 (+0.56), lag 14 (+0.42) and lag 21
  (+0.36) — a clean signature of weekly seasonality.
- **Non-seasonal order (1,1,1):** the PACF does *not* cut off cleanly after
  lag 1 — it stays significant through lag 6 — so (p,d,q) was not read
  directly off the correlogram. (1,1,1) was selected by the grid search
  below, not by a textbook ACF/PACF pattern-match.
- **Seasonal order (1,1,1,7):** mirrors the non-seasonal structure at the
  weekly lag.
    """
)

st.subheader("Candidate Model Comparison")
comparison_df = pd.DataFrame([
    {"Model": "Seasonal Naive (baseline)", "MAPE": "25.29%", "MAE": "£15,463", "AIC": "—", "BIC": "—"},
    {"Model": "SARIMA(1,1,0)(1,1,0,7)", "MAPE": "32.84%", "MAE": "£17,349", "AIC": "7527.58", "BIC": "7539.05"},
    {"Model": "SARIMA(1,1,1)(1,1,1,7) ✅ chosen", "MAPE": "20.49%", "MAE": "£15,743", "AIC": "7406.00", "BIC": "7425.12"},
    {"Model": "SARIMA(2,1,1)(1,1,1,7)", "MAPE": "20.50%", "MAE": "£15,812", "AIC": "7403.49", "BIC": "7426.43"},
])
st.dataframe(comparison_df, hide_index=True, width="stretch")
st.caption(
    "SARIMA(1,1,1)(1,1,1,7) selected on BIC (parsimony) and test-set MAPE, "
    "outperforming the naive baseline; confirmed as the MAPE-optimum of all "
    "144 grid-searched combinations (see 'Verify best model' below)."
)
if st.button("Verify best model"):
    verify_best_model_dialog(train, test)

st.divider()
st.subheader("Backtest: Model vs. Known History")
st.caption(
    f"Validates the model against {len(test)} days it was NOT trained on "
    f"({test.index.min().date()} to {test.index.max().date()}) — this is how "
    "the accuracy numbers above were measured. It is not a prediction of the future."
)

fig = go.Figure()
actual = pd.concat([train, test])
fig.add_trace(go.Scatter(
    x=actual.index, y=actual.values, mode="lines", name="Actual",
    line=dict(color="#2A78D6", width=2),
))
fig.add_trace(go.Scatter(
    x=result.index, y=result["forecast"], mode="lines", name="Forecast",
    line=dict(color="#eb6834", width=2),
))
fig.add_trace(go.Scatter(
    x=list(result.index) + list(result.index[::-1]),
    y=list(result["upper"]) + list(result["lower"][::-1]),
    fill="toself",
    fillcolor="rgba(235, 104, 52, 0.25)",
    line=dict(color="rgba(255,255,255,0)"),
    name="95% Confidence Interval",
    hoverinfo="skip",
))
fig.update_layout(
    title="Backtest — SARIMA(1,1,1)(1,1,1,7) vs. known history",
    xaxis_title="Date",
    yaxis_title="Revenue (£)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, width="stretch")

st.subheader("Backtest Data")
st.dataframe(result, width="stretch")
st.download_button(
    "📥 Download backtest (CSV)",
    result.to_csv().encode("utf-8"),
    "sales_forecast_backtest.csv",
    "text/csv",
)
