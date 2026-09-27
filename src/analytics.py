"""Aggregations for the Sales Analytics page. No Streamlit code here — testable in isolation."""

from __future__ import annotations
import pandas as pd

def kpis(df: pd.DataFrame) -> dict:
    """Headline numbers for the KPI row."""

    return {
        "revenue": df["Revenue"].sum(),          # <- dict key can stay lowercase, it's just a label
        "orders": df["InvoiceNo"].nunique(),
        "units": df["Quantity"].sum(),
        "customers": df.loc[df["HasCustomer"], "CustomerID"].nunique(),
        "aov": df["Revenue"].sum() / df["InvoiceNo"].nunique() if len(df) else 0.0,
        "countries": df["Country"].nunique(),
    }

def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """One row per YearMonth: Revenue, Orders. Sorted chronologically."""
    out = (
        df.groupby("YearMonth", observed=True)
        .agg(
            Revenue=("Revenue", "sum"), 
            Orders=("InvoiceNo", "nunique")
        )
        .reset_index()
        .sort_values("YearMonth")
    )
    return out

def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top n products by revenue, descending."""
    return (
        df.groupby("Product", observed=True)["Revenue"]
        .sum()
        .nlargest(n)
        .reset_index()
    )

def revenue_by_country(df: pd.DataFrame, exclude_uk: bool = False) -> pd.DataFrame:
    """Revenue per country, descending. UK usually dwarfs everyone else on this dataset."""

    out = df.groupby("Country", observed=True)["Revenue"].sum().reset_index()
    if exclude_uk:
        out = out[out["Country"]] != "Unitded kingdom"

    return out.sort_values("Revenue", ascending=False)

def revenue_by_country(df: pd.DataFrame, exclude_uk: bool = False) -> pd.DataFrame:
    """Revenue per country, descending. UK usually dwarfs everyone else on this dataset."""
    out = df.groupby("Country", observed=True)["Revenue"].sum().reset_index()
    if exclude_uk:
        out = out[out["Country"] != "United Kingdom"]
    return out.sort_values("Revenue", ascending=False)

def apply_filters(
    df: pd.DataFrame,
    countries: list[str] | None = None,
    years: list[int] | None = None,
    months: list[int] | None = None,
) -> pd.DataFrame:
    """Return the rows matching all given filters. Empty/None list = no filter on that field."""
    out = df
    if countries:
        out = out[out["Country"].isin(countries)]
    if years:
        out = out[out["Year"].isin(years)]
    if months:
        out = out[out["Month"].isin(months)]
    return out