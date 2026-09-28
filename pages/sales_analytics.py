import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import analytics, config, ui
from src.data_loader import load_processed

REVENUE_COLOR = config.REVENUE_COLOR
ORDERS_COLOR = config.ORDERS_COLOR
GRID_COLOR = config.GRID_COLOR

st.title("Sales Analytics")
st.caption("Filter, explore and export UK/EU e-commerce transactions from the UCI Online Retail dataset.")

try:
    df = load_processed()
except FileNotFoundError:
    st.warning("Analysis dataset not built yet.")
    st.code("python scripts/build_dataset.py", language="bash")
    st.stop()

# --- Filters (sidebar) ---------------------------------------------------
st.sidebar.header("Filters")
countries = st.sidebar.multiselect("Country", sorted(df["Country"].unique()))
date_range = ui.date_range_filter(df["Date"])
base = analytics.apply_filters(df, countries=countries, date_range=date_range)

# --- Click-to-filter: selections made on the charts during the previous run ---
country_key = ui.chart_key("country_chart")
product_key = ui.chart_key("product_chart")
picked_countries = ui.selected_points(country_key, "x")
picked_products = ui.selected_points(product_key, "y")
ui.clear_selection_button(bool(picked_countries or picked_products))

if base.empty:
    st.warning("No transactions match these filters. Try widening your selection.")
    st.stop()

# Each chart ignores its own selection (so its bars stay put) but obeys the other's.
filtered = analytics.apply_filters(base, countries=picked_countries, products=picked_products)
if filtered.empty:
    st.warning("No transactions match the chart selection. Use 'Clear chart selection' in the sidebar.")
    st.stop()

if picked_countries or picked_products:
    active = [f"Country: {', '.join(picked_countries)}" if picked_countries else "",
              f"Product: {', '.join(picked_products)}" if picked_products else ""]
    st.info("Chart selection active, " + " | ".join(a for a in active if a))


def styled_chart(fig: go.Figure) -> go.Figure:
    """One shared look for every chart on this page: clean surface, recessive grid, no legend clutter."""
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="sans-serif", size=13, color="#0b0b0b"),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=GRID_COLOR)
    fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False)
    return fig


# --- KPI row -----------------------------------------------------------
st.markdown("### Key Metrics")
k = analytics.kpis(filtered)
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Revenue", f"£{k['revenue']:,.0f}")
c2.metric("Orders", f"{k['orders']:,}")
c3.metric("Units", f"{k['units']:,}")
c4.metric("Customers", f"{k['customers']:,}")
c5.metric("AOV", f"£{k['aov']:,.2f}")
c6.metric("Countries", f"{k['countries']:,}")

st.divider()

# --- Charts (2x2 grid) ---------------------------------------------------
monthly = analytics.monthly_revenue(filtered)
top_n = st.radio("Top products: show", [5, 10, 20], horizontal=True, index=1)
top = analytics.top_products(analytics.apply_filters(base, countries=picked_countries), n=top_n).sort_values("Revenue")
st.session_state.setdefault("exclude_uk", True)
exclude_uk = st.checkbox("Exclude United Kingdom from country chart", key="exclude_uk")
by_country = analytics.revenue_by_country(
    analytics.apply_filters(base, products=picked_products), exclude_uk=exclude_uk
)
st.caption("Click a country or product bar to filter the whole page (shift-click for several).")

row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.markdown("**Monthly Revenue**")
    fig = px.line(monthly, x="YearMonth", y="Revenue", markers=True)
    fig.update_traces(line_color=REVENUE_COLOR, line_width=2, marker=dict(size=8, color=REVENUE_COLOR))
    st.plotly_chart(styled_chart(fig), width="stretch")
with row1_col2:
    st.markdown("**Orders by Month**")
    fig = px.bar(monthly, x="YearMonth", y="Orders")
    fig.update_traces(marker_color=ORDERS_COLOR)
    st.plotly_chart(styled_chart(fig), width="stretch")

row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.markdown("**Top Products**")
    fig = px.bar(top, x="Revenue", y="Product", orientation="h")
    fig.update_traces(marker_color=REVENUE_COLOR)
    st.plotly_chart(
        styled_chart(fig), width="stretch", key=product_key, on_select="rerun", selection_mode="points"
    )
with row2_col2:
    st.markdown("**Revenue by Country**")
    fig = px.bar(by_country.head(15), x="Country", y="Revenue")
    fig.update_traces(marker_color=REVENUE_COLOR)
    st.plotly_chart(
        styled_chart(fig), width="stretch", key=country_key, on_select="rerun", selection_mode="points"
    )

st.divider()

# --- Transaction explorer ---------------------------------------------------
cols = ["InvoiceNo", "Date", "Country", "Product", "Quantity", "UnitPrice", "Revenue"]
st.markdown("### Transaction Explorer")
st.caption(f"{len(filtered):,} rows")
st.dataframe(filtered[cols], hide_index=True, width="stretch")
st.download_button(
    "Download filtered transactions (CSV)",
    filtered[cols].to_csv(index=False).encode("utf-8"),
    file_name="transactions.csv",
    mime="text/csv",
)
