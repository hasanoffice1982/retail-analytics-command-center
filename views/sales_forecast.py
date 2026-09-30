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
)
import plotly.graph_objects as go

st.title("Sales Forecast")

df = load_processed()
daily = aggregate_daily(df)
train, test = train_test_split_series(daily)

model = fit_sarima(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))
result = forecast_with_ci(model, steps=len(test))
result["lower"] = result["lower"].clip(lower=0)

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
