import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.data_loader import load_processed
from src.forecasting import aggregate_daily, fit_sarima, forecast_with_ci

st.title("Sales Forecast")

FORWARD_HORIZON = 84  # 12 weeks


@st.cache_data(show_spinner="Fitting forward-looking model on full history...")
def get_forward_forecast(daily: pd.Series, steps: int):
    full_model = fit_sarima(daily, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))
    future = forecast_with_ci(full_model, steps=steps)
    future["lower"] = future["lower"].clip(lower=0)
    return future


df = load_processed()
daily = aggregate_daily(df)
future = get_forward_forecast(daily, FORWARD_HORIZON)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Forecast Horizon", f"{FORWARD_HORIZON} days")
with col2:
    next_week_total = future["forecast"].iloc[:7].sum()
    st.metric("Next 7 Days", f"£{next_week_total:,.0f}")
with col3:
    next_4w_total = future["forecast"].iloc[:28].sum()
    st.metric("Next 4 Weeks", f"£{next_4w_total:,.0f}")

st.caption(
    "Model: SARIMA(1,1,1)(1,1,1,7), backtested at 20.49% MAPE on 28 days of "
    "held-out history. See the Methodology page for validation details, error "
    "analysis and model selection rationale."
)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=daily.index, y=daily.values, mode="lines", name="Actual (history)",
    line=dict(color="#2A78D6", width=2),
))
fig.add_trace(go.Scatter(
    x=future.index, y=future["forecast"], mode="lines", name="Forecast (future)",
    line=dict(color="#eb6834", width=2),
))
fig.add_trace(go.Scatter(
    x=list(future.index) + list(future.index[::-1]),
    y=list(future["upper"]) + list(future["lower"][::-1]),
    fill="toself",
    fillcolor="rgba(235, 104, 52, 0.25)",
    line=dict(color="rgba(255,255,255,0)"),
    name="95% Confidence Interval",
    hoverinfo="skip",
))
fig.update_layout(
    title=f"Forward Forecast from {daily.index.max().date()}",
    xaxis_title="Date",
    yaxis_title="Revenue (£)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig, width="stretch")

st.subheader("Forecast Data")
st.dataframe(future, width="stretch")
st.download_button(
    "📥 Download forecast (CSV)",
    future.to_csv().encode("utf-8"),
    "sales_forecast.csv",
    "text/csv",
)
