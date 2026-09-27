"""Build the analysis dataset. Run: python scripts/build_dataset.py"""

import pandas as pd
import pytest

from src.data_loader import DataValidationError, validate_schema
from src.preprocessing import clean


def make_raw() -> pd.DataFrame:
    rows = [
        # InvoiceNo, StockCode, Description, Qty, Date, Price, Cust, Country
        (
            "1001",
            "A1",
            " Mug ",
            2,
            "2010-12-01 08:26",
            3.0,
            "111",
            "United Kingdom",
        ),  # valid
        (
            "1001",
            "A1",
            " Mug ",
            2,
            "2010-12-01 08:26",
            3.0,
            "111",
            "United Kingdom",
        ),  # duplicate
        (
            "1002",
            "B2",
            "Plate",
            1,
            "2010-12-02 09:00",
            5.0,
            None,
            "France",
        ),  # no customer, kept
        (
            "C1003",
            "A1",
            "Mug",
            -2,
            "2010-12-03 10:00",
            3.0,
            "111",
            "United Kingdom",
        ),  # cancellation
        (
            "1004",
            "C3",
            "Bowl",
            -1,
            "2010-12-04 10:00",
            2.0,
            "112",
            "France",
        ),  # negative qty
        (
            "1005",
            "D4",
            "Cup",
            1,
            "2010-12-05 10:00",
            0.0,
            "113",
            "France",
        ),  # zero price
        (
            "1006",
            "POST",
            "Postage",
            1,
            "2010-12-06 10:00",
            18.0,
            "114",
            "France",
        ),  # non-product
        ("1007", "E5", "Fork", 1, "not-a-date", 2.0, "115", "France"),  # bad date
    ]

    cols = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ]

    return pd.DataFrame(rows, columns=cols).astype(
        {"InvoiceNo": "string", "StockCode": "string", "CustomerID": "string"}
    )


def test_clean_keeps_only_vlaid_slaes():
    df, report = clean(make_raw())

    assert set(df["InvoiceNo"]) == {"1001", "1002"}
    removed = {r["step"]: r["rows_removed"] for r in report}
    assert removed["duplicates"] == 1
    assert removed["cancelled_invoices"] == 1
    assert removed["invalid_quantity"] == 1
    assert removed["invalid_price"] == 1
    assert removed["non_product_codes"] == 1
    assert removed["unparseable_values"] == 1

def test_revenue_and_customer_flag():
    df, _ = clean(make_raw())
    mug = df[df["InvoiceNo"] == "1001"].iloc[0]
    assert mug["Revenue"] == 6.0
    assert mug["Product"] == "MUG"
    assert not df.loc[df["InvoiceNo"] == "1002", "HasCustomer"].iloc[0]

def test_input_not_mutated():
    raw = make_raw()
    snapshot = raw.copy(deep=True)
    clean(raw)
    pd.testing.assert_frame_equal(raw, snapshot)

def test_schema_validation():
    with pytest.raises(DataValidationError):
        validate_schema(pd.DataFrame({"InvoiceNo": ["1"]}))