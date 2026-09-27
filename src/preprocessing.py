from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from src import config


def _log(report: list[dict], step: str, before: int, after: int, why: str) -> None:
    report.append(
        {"step": step, "rows_before": before, "rows_after": after, "rationale": why}
    )


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Return (analysis_df, report). The input DataFrame is not modified."""
    report: list[dict] = []
    df = raw.copy()
    _log(report, "raw", len(df), len(df), "Untouched raw records")

    # 1. Bad values become NaN/NaT, then drop them
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    n = len(df)
    df = df.dropna(subset=["InvoiceDate", "Quantity", "UnitPrice", "InvoiceNo", "StockCode"])
    _log(report, "unparseable_values", n, len(df), "Missing/invalid date, quantity, price or IDs")

    # Exact duplicates
    n = len(df)
    df = df.drop_duplicates()
    _log(report, "duplicates", n, len(df), "Exact duplicate records")

    # Cancellations
    n = len(df)
    df = df[~df["InvoiceNo"].str.upper().str.startswith(config.CANCELLATION_PREFIX)]
    _log(report, "cancelled_invoices", n, len(df), "Invoices prefixed 'C'")

    # Invalid quantity / price
    n = len(df)
    df = df[df["Quantity"] > 0]
    _log(report, "invalid_quantity", n, len(df), "Quantity <= 0")

    n = len(df)
    df = df[df["UnitPrice"] > 0]
    _log(report, "invalid_price", n, len(df), "UnitPrice <= 0")

    # Non-product codes
    n = len(df)
    df = df[~df["StockCode"].str.upper().isin(config.NON_PRODUCT_CODES)]
    _log(report, "non_product_codes", n, len(df), "Postage, fees, manual adjustments")

    df["HasCustomer"] = df["CustomerID"].notna()

    # Features
    df["Product"] = df["Description"].fillna("UNKNOWN").str.strip().str.upper()
    df["Revenue"] = (df["Quantity"] * df["UnitPrice"]).round(2)
    df["Date"] = df["InvoiceDate"].dt.normalize()
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit="D")  # Monday start

    return df.sort_values("InvoiceDate").reset_index(drop=True), report

