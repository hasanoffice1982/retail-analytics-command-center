import json

import pandas as pd
import streamlit as st

from src import config
from src.data_loader import load_processed

st.title("Retail Analytics Command Center")
st.caption("Sales analytics and forecasting on the UCI Online Retail dataset.")

try:
    df = load_processed()
except FileNotFoundError:
    st.warning("Analysis dataset not built yet.")
    st.code("python scripts/build_dataset.py", language="bash")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"£{df['Revenue'].sum():,.0f}")
c2.metric("Orders", f"{df['InvoiceNo'].nunique():,}")
c3.metric("Customers", f"{df.loc[df['HasCustomer'], 'CustomerID'].nunique():,}")
c4.metric("Countries", f"{df['Country'].nunique():,}")

st.subheader("Data cleaning report")
if config.CLEANING_REPORT_FILE.exists():
    report = pd.DataFrame(json.loads(config.CLEANING_REPORT_FILE.read_text()))
    st.dataframe(report, hide_index=True, width="stretch")