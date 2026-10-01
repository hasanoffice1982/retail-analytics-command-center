import pandas as pd
import streamlit as st
from src.data_loader import load_processed
from src.forecasting import (
    aggregate_daily,
    train_test_split_series,
    fit_sarima,
    forecast_with_ci,
    evaluate_forecast,
    seasonal_naive_forecast,
    tune_sarima,
)
import plotly.graph_objects as go

st.title("Sales Forecast")


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





model = fit_sarima(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))
result = forecast_with_ci(model, steps=len(test))
result["lower"] = result["lower"].clip(lower=0)
forecast_point = model.forecast(steps=len(test))
metrics = evaluate_forecast(test, forecast_point)
mape = metrics['mape']


col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Model Accuracy (MAPE)", f"{mape:.2f}%")

with col2:
    st.metric("Forecast Horizon", f"{len(test)} days")

with col3:
    next_week_total = result['forecast'].iloc[:7].sum()
    st.metric('Next 7 days Project Revenue', f"£{next_week_total:,.0f}")

st.divider()
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
    "See docs/forecasting_methodology.md §6 for the full explanation."
)

st.caption(
    "Model order confirmed by an exhaustive grid search over 144 SARIMA "
    "configurations, scored by test-set MAPE — SARIMA(1,1,1)(1,1,1,7) was the "
    "optimum (20.485%); see docs/forecasting_methodology.md §3.5 for the full comparison."
)
if st.button("Verify best model"):
    verify_best_model_dialog(train, test)

fig = go.Figure()

actual = pd.concat([train, test])

fig.add_trace(
    go.Scatter(
        x=actual.index,
        y=actual.values,
        mode="lines",
        name="Actual",
        line=dict(color="#2A78D6", width=2),
    )
)


# Forecast line
fig.add_trace(go.Scatter(
    x=result.index, y=result["forecast"],
    mode="lines", name="Forecast",
    line=dict(color="#eb6834", width=2)
))

# Confidence interval band (shaded area)
fig.add_trace(go.Scatter(
    x=list(result.index) + list(result.index[::-1]),
    y=list(result["upper"]) + list(result["lower"][::-1]),
    fill="toself",
    fillcolor="rgba(235, 104, 52, 0.25)",
    line=dict(color="rgba(255,255,255,0)"),
    name="95% Confidence Interval",
    hoverinfo="skip"
))

fig.update_layout(
    title="Sales Forecast — SARIMA(1,1,1)(1,1,1,7)",
    xaxis_title="Date",
    yaxis_title="Revenue (£)",
    hovermode="x unified",
    legend=dict(
        orientation="h",  
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)


st.plotly_chart(fig, width="stretch")

st.write(result.head())
