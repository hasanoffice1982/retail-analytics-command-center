import streamlit as st

st.set_page_config(page_title="Retail Analytics Command Center", page_icon="📊", layout="wide")

# Global control sizing (runs once, applies to every page). Streamlit has no
# native "size" option for radio/checkbox, so this scales the widget and
# enlarges its label text app-wide instead of per-page CSS.
st.markdown(
    """
    <style>
    div[data-testid="stRadio"] label,
    div[data-testid="stCheckbox"] label {
        font-size: 1.15rem;
    }
    div[data-testid="stRadio"] label [data-baseweb="radio"] > div:first-child,
    div[data-testid="stCheckbox"] label [data-baseweb="checkbox"] > div:first-child {
        transform: scale(1.4);
        transform-origin: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
pages = [
    st.Page("pages/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("pages/sales_analytics.py", title="Sales Analytics", icon="📊"),
]
st.navigation(pages).run()