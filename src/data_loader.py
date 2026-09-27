"""Raw data access. Reads and validates only; never modifies files in data/raw/."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):  # executed directly: python src/data_loader.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config

logger = logging.getLogger(__name__)


class DataValidationError(ValueError):
    """Raised when the raw data does not match the expected schema."""


def find_raw_file(raw_dir: Path = config.RAW_DIR) -> Path:
    """Return the first existing raw file listed in config.RAW_CANDIDATES."""
    for name in config.RAW_CANDIDATES:
        candidate = raw_dir / name
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"No raw dataset in {raw_dir}. Expected one of {config.RAW_CANDIDATES}."
    )


def validate_schema(df: pd.DataFrame) -> None:
    """Fail early with a clear message if required columns are missing or data is empty."""
    missing = [c for c in config.REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")
    if df.empty:
        raise DataValidationError("Raw data is empty.")


def _normalize_customer_id(series: pd.Series) -> pd.Series:
    """17850.0 -> '17850'; missing stays <NA>."""
    return pd.to_numeric(series, errors="coerce").astype("Int64").astype("string")


def load_raw(path: Path | None = None) -> pd.DataFrame:
    """Read the raw dataset (csv), normalize columns and validate the schema."""
    path = Path(path) if path else find_raw_file()
    logger.info("Loading raw data from %s", path)

    df = pd.read_csv(
        path, encoding="utf-8", encoding_errors="replace", parse_dates=["InvoiceDate"]
    )

    df = df.rename(columns=config.COLUMN_RENAMES)
    
    validate_schema(df)

    df["CustomerID"] = _normalize_customer_id(df["CustomerID"])

    for col in ("InvoiceNo", "StockCode"):
        df[col] = df[col].astype("string")

    return df


