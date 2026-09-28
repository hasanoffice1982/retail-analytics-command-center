"""Central configuration: paths, schema and cleaning rules.

Nothing else in the project should hardcode a path, column name or rule.
"""
from __future__ import annotations
from pathlib import Path

# Path===============

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RAW_CANDIDATES = ("online_retail.csv",)
PROCESSED_FILE = PROCESSED_DIR / "retail_clean.parquet"
CLEANING_REPORT_FILE = PROCESSED_DIR / "cleaning_report.json"

# SCHEMA==========
COLUMN_RENAMES = {
    "Invoice": "InvoiceNo",
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
}

REQUIRED_COLUMNS = (
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
)

# --- Cleaning rules ------------------------------------------------------
# --- Chart colors (validated: node scripts/validate_palette.js) --------
# Single source for every page's charts. Do not redefine these locally.
REVENUE_COLOR = "#2a78d6"  # blue: every money-based chart
ORDERS_COLOR = "#eb6834"  # orange: the one count-based chart
GRID_COLOR = "#e6e5e0"  # recessive gridlines

CANCELLATION_PREFIX = "C"

NON_PRODUCT_CODES = (
    "POST",
    "D",
    "DOT",
    "M",
    "BANK CHARGES",
    "AMAZONFEE",
    "S",
    "B",
    "CRUK",
    "PADS",
)
