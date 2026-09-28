"""Streamlit helpers shared by every page (filters, chart selections, drilldown)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

SALES_PAGE = "pages/sales_analytics.py"


def date_range_filter(dates: pd.Series) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Sidebar date-range picker. Same widget key on every page, so the range carries across pages."""
    lo, hi = dates.min().date(), dates.max().date()
    picked = st.sidebar.date_input(
        "Date range", value=(lo, hi), min_value=lo, max_value=hi, key="date_range"
    )
    if len(picked) != 2:  # user has picked the start date but not the end yet
        st.info("Pick an end date to apply the date range.")
        st.stop()
    return pd.Timestamp(picked[0]), pd.Timestamp(picked[1])


def chart_key(name: str) -> str:
    """Selection-state key for a chart. Bumping the version resets every chart selection."""
    return f"{name}_{st.session_state.get('selection_version', 0)}"


def selected_points(key: str, axis: str) -> list:
    """Values picked on a chart's `axis` ('x' or 'y') during the previous run."""
    state = st.session_state.get(key)
    if not state:
        return []
    return [point[axis] for point in state["selection"]["points"]]


def _reset_selections() -> None:
    st.session_state["selection_version"] = st.session_state.get("selection_version", 0) + 1


def clear_selection_button(active: bool) -> None:
    """Sidebar button that clears all chart click-selections. Hidden when nothing is selected."""
    if active:
        st.sidebar.button("Clear chart selection", on_click=_reset_selections, width="stretch")


def drill_to_sales(exclude_uk: bool = True) -> None:
    """Jump to Sales Analytics; the date range carries over via the shared widget key."""
    st.session_state["exclude_uk"] = exclude_uk
    st.switch_page(SALES_PAGE)
