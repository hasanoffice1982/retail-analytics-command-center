import pandas as pd
import pytest

from src import analytics


def make_df() -> pd.DataFrame:
    rows = [
        # InvoiceNo, Country, Year, Month, YearMonth, Product, Quantity, Revenue, CustomerID, HasCustomer
        ("1", "France", 2011, 1, "2011-01", "MUG", 2, 10.0, "A", True),
        ("2", "France", 2011, 2, "2011-02", "MUG", 1, 5.0, "B", True),
        ("3", "Germany", 2011, 1, "2011-01", "PLATE", 3, 30.0, None, False),
        ("4", "United Kingdom", 2010, 12, "2010-12", "BOWL", 1, 8.0, "C", True),
    ]
    cols = ["InvoiceNo", "Country", "Year", "Month", "YearMonth", "Product",
            "Quantity", "Revenue", "CustomerID", "HasCustomer"]
    return pd.DataFrame(rows, columns=cols)


def test_kpis():
    result = analytics.kpis(make_df())
    assert result["revenue"] == 53.0
    assert result["orders"] == 4
    assert result["customers"] == 3          # excludes the HasCustomer=False row
    assert result["countries"] == 3
    assert result["aov"] == 53.0 / 4


def test_kpis_empty_df_no_zero_division():
    empty = make_df().iloc[0:0]
    result = analytics.kpis(empty)
    assert result["aov"] == 0.0


def test_monthly_revenue():
    result = analytics.monthly_revenue(make_df())
    jan_2011 = result[result["YearMonth"] == "2011-01"].iloc[0]
    assert jan_2011["Revenue"] == 40.0        # 10.0 (France) + 30.0 (Germany)
    assert jan_2011["Orders"] == 2


def test_top_products():
    result = analytics.top_products(make_df(), n=2)
    assert result.iloc[0]["Product"] == "PLATE"   # 30.0, highest
    assert len(result) == 2


def test_revenue_by_country_exclude_uk():
    result = analytics.revenue_by_country(make_df(), exclude_uk=True)
    assert "United Kingdom" not in result["Country"].values
    assert set(result["Country"]) == {"France", "Germany"}


def test_apply_filters_country_and_year():
    result = analytics.apply_filters(make_df(), countries=["France"], years=[2011])
    assert len(result) == 2
    assert set(result["Country"]) == {"France"}


def test_apply_filters_no_filters_returns_everything():
    result = analytics.apply_filters(make_df())
    assert len(result) == 4