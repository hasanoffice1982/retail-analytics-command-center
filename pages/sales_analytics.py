from src.data_loader import load_processed
from src import analytics

df = load_processed()
print(analytics.kpis(df))
print(analytics.monthly_revenue(df).head())
print(analytics.top_products(df, 5))
print(analytics.revenue_by_country(df, exclude_uk=True).head())

filtered = analytics.apply_filters(df, countries=["France"], years=[2011])
print(analytics.kpis(filtered))