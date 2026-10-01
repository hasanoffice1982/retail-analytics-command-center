import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src import analytics, config, ui
from src.data_loader import load_processed

# UCI Online Retail uses non-standard country labels; map to the names Plotly's
# choropleth recognizes. Values not in either list are excluded from the map
# below (not real countries, or <0.3% of revenue combined — see caption).
COUNTRY_NAME_FIXES = {"EIRE": "Ireland", "RSA": "South Africa", "USA": "United States"}
NON_COUNTRY_VALUES = {"European Community", "Unspecified", "Channel Islands"}

st.title("Retail Analytics Command Center")
st.caption("Sales analytics and forecasting on the UCI Online Retail dataset.")

try:
    df = load_processed()
except FileNotFoundError:
    st.warning("Analysis dataset not built yet.")
    st.code("python scripts/build_dataset.py", language="bash")
    st.stop()

st.sidebar.header("Filters")
filtered = analytics.apply_filters(df, date_range=ui.date_range_filter(df["Date"]))
if filtered.empty:
    st.warning("No transactions in this date range.")
    st.stop()

# --- KPI cards: each one drills down into Sales Analytics (date range carries over) ---
k = analytics.kpis(filtered)
cards = [
    ("Revenue", f"£{k['revenue']:,.0f}", True),
    ("Orders", f"{k['orders']:,}", True),
    ("Customers", f"{k['customers']:,}", True),
    ("Countries", f"{k['countries']:,}", False),  # show every country, UK included
]
for col, (label, value, exclude_uk) in zip(st.columns(len(cards)), cards):
    col.metric(label, value)
    if col.button("Explore →", key=f"drill_{label}", width="stretch"):
        ui.drill_to_sales(exclude_uk=exclude_uk)

st.subheader("🌍 Revenue by Country")
country_revenue = (
    filtered[~filtered["Country"].isin(NON_COUNTRY_VALUES)]
    .assign(Country=lambda d: d["Country"].replace(COUNTRY_NAME_FIXES))
    .groupby("Country")
    .agg(
        revenue=("Revenue", "sum"),
        orders=("InvoiceNo", "nunique"),
        customers=("CustomerID", "nunique"),
    )
    .reset_index()
)
country_revenue["log_revenue"] = np.log10(country_revenue["revenue"].clip(lower=1))

fig_map = px.choropleth(
    country_revenue,
    locations="Country",
    locationmode="country names",
    color="log_revenue",
    hover_name="Country",
    hover_data={"log_revenue": False, "revenue": ":,.0f", "orders": ":,", "customers": ":,"},
    color_continuous_scale="Blues",  # single hue, light->dark — correct convention for sequential data
)
fig_map.update_layout(
    coloraxis_colorbar=dict(title="Revenue<br>(log scale)", tickformat=".1s"),
    margin=dict(l=0, r=0, t=0, b=0),
    geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
)
st.plotly_chart(fig_map, width="stretch")
st.caption(
    "Color scale is logarithmic — the UK accounts for the large majority of "
    "revenue, so a linear scale would hide every other country's pattern. "
    "Excludes non-country values (European Community, Unspecified, Channel "
    "Islands — together <0.3% of revenue)."
)

st.subheader("Revenue Trend")
monthly = filtered.set_index("InvoiceDate").resample("ME")["Revenue"].sum()
st.line_chart(monthly)

st.subheader("Explore the App")
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    st.markdown("**📊 Sales Analytics**\n\nFilters, charts and click-to-filter drill-down on product, country and time.")
with nav_col2:
    st.markdown("**📈 Sales Forecast**\n\nSARIMA-based forecast, baseline comparison, and model methodology.")
with nav_col3:
    st.markdown("**🧪 Stratified Sampling**\n\nResearch-grade representative sampling from the full dataset.")

st.subheader("Data cleaning report")
if config.CLEANING_REPORT_FILE.exists():
    report = pd.DataFrame(json.loads(config.CLEANING_REPORT_FILE.read_text()))
    st.dataframe(report, hide_index=True, width="stretch")
else:
    st.info("No cleaning report yet. Run: python scripts/build_dataset.py")
