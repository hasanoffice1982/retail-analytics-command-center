import streamlit as st

st.set_page_config(page_title="Retail Analytics Command Center", page_icon="📊", layout="wide")
pages = [st.Page("pages/overview.py", title="Overview", icon="🏠", default=True)]
st.navigation(pages).run()