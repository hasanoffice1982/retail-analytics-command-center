import json

import pandas as pd
import streamlit as st

from src import analytics, config, ui
from src.data_loader import load_processed

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

st.subheader("Data cleaning report")
if config.CLEANING_REPORT_FILE.exists():
    report = pd.DataFrame(json.loads(config.CLEANING_REPORT_FILE.read_text()))
    st.dataframe(report, hide_index=True, width="stretch")
else:
    st.info("No cleaning report yet. Run: python scripts/build_dataset.py")
