import pandas as pd

from src.analytics import apply_filters


def make_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(["2010-12-01", "2010-12-15", "2011-01-10"]),
            "Country": ["France", "Germany", "France"],
            "Product": ["MUG", "BOWL", "BOWL"],
            "Year": [2010, 2010, 2011],
            "Month": [12, 12, 1],
        }
    )


def test_date_range_is_inclusive():
    out = apply_filters(make_df(), date_range=(pd.Timestamp("2010-12-01"), pd.Timestamp("2010-12-15")))
    assert len(out) == 2


def test_product_and_country_filters_combine():
    out = apply_filters(make_df(), countries=["France"], products=["BOWL"])
    assert list(out["Date"].dt.strftime("%Y-%m-%d")) == ["2011-01-10"]


def test_empty_filters_keep_everything():
    assert len(apply_filters(make_df(), countries=[], products=[], date_range=None)) == 3
