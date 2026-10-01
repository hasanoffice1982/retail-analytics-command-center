import streamlit as st

from src import config

st.set_page_config(page_title="Retail Analytics Command Center", page_icon="📊", layout="wide")

st.markdown(
    f"""
    <style>
    div[data-testid="stButtonGroup"] [role="radiogroup"] {{
        display: inline-flex;
        gap: 4px;
        padding: 5px;
        background: #eef1f6;
        border: 1px solid #dde3ec;
        border-radius: 999px;
    }}
    div[data-testid="stButtonGroup"] button[data-variant="segmented_control"] {{
        min-height: 2.75rem;
        padding: 0 1.75rem;
        border: none !important;
        border-radius: 999px !important;
        background: transparent !important;
        transition: background 0.15s ease, box-shadow 0.15s ease;
    }}
    div[data-testid="stButtonGroup"] button[data-variant="segmented_control"] p {{
        font-size: 1.1rem;
        font-weight: 600;
        color: #3b4a5e;
    }}
    div[data-testid="stButtonGroup"] button[data-variant="segmented_control"]:hover {{
        background: #e1e7f0 !important;
    }}
    div[data-testid="stButtonGroup"] button[data-selected="true"] {{
        background: {config.REVENUE_COLOR} !important;
        box-shadow: 0 2px 8px rgba(42, 120, 214, 0.35);
    }}
    div[data-testid="stButtonGroup"] button[data-selected="true"] p {{
        color: #ffffff;
    }}
    div[data-testid="stToggle"] label p,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stRadio"] label p {{
        font-size: 1.1rem;
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 1.6rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

pages = [
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("views/sales_analytics.py", title="Sales Analytics", icon="📊"),
    st.Page("views/sales_forecast.py", title="Sales Forecast", icon="📈"),
    st.Page("views/methodology.py", title="Methodology", icon="🔬"),
]

st.navigation(pages).run()
