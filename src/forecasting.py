import pandas as pd
from src.data_loader import load_processed
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt
import numpy as np


def aggregate_daily(df: pd.DataFrame) -> pd.Series:
    """
    Collapse transaction-level rows into one daily revenue series.

    Input:  the cleaned analysis DataFrame (has 'Date' and 'Revenue').
    Output: a pandas Series, indexed by every calendar day in range
            (no gaps — including Saturdays, which this dataset has zero
            revenue for), values = summed Revenue for that day.

    Hint: group by 'Date', sum 'Revenue', then reindex against a full
    date range (pd.date_range) so there are no missing days — missing
    days must become 0, not be silently absent, or the model will
    misread the calendar.
    """
    daily = df.groupby('Date')['Revenue'].sum()
    full_range  = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq='D')
    daily = daily.reindex(full_range)
    daily = daily.fillna(0)

    return daily


def train_test_split_series(daily: pd.Series, test_days: int = 28) -> tuple[pd.Series, pd.Series]:
    """
    Split a daily series chronologically into train/test.
    Input:  the full daily revenue Series (output of aggregate_daily).
    test_days: how many of the most recent days to hold out for testing.
    Output: (train, test) — two Series, train is everything before the
            cutoff, test is the last `test_days` days. No overlap, no gaps.
    """
    split_point = int(len(daily) - test_days)
    train = daily.iloc[:split_point]
    test = daily.iloc[split_point:]

    return train, test

def check_stationarity(series: pd.Series) -> dict:
    """
    Run the Augmented Dickey-Fuller test on a time series.
    Input:  a pandas Series (e.g. the training daily revenue).
    Output: a dict with keys: 'adf_statistic', 'p_value', 'is_stationary'
            (is_stationary = True if p_value < 0.05).
    """
    adf = adfuller(series, result_object=True)
    adf_statistic, p_vlaue = adf.statistic, adf.pvalue
    return {
        'adf_statistic': adf_statistic,
        'p_value': p_vlaue,
        'is_stationary': p_vlaue < 0.05
    }


def seasonal_naive_forecast(train: pd.Series, test: pd.Series, season: int = 7) -> pd.Series:
    """
    Baseline forecast: predict each test-period value as the actual value
    from `season` days earlier.
    Input:  train (history), test (the period to forecast), season (7 = weekly).
    Output: a pandas Series, same index as `test`, containing the predicted values.
    """

    combined = pd.concat([train, test])
    shifted = combined.shift(season)
    forcast = shifted.loc[test.index]

    return forcast


def evaluate_forecast(
    actual: pd.Series, predicted: pd.Series, train: pd.Series | None = None, season: int = 7
) -> dict:
    """
    Compare a forecast against actual values.

    Input:  actual (test set, ground truth), predicted (forecast, same index/length).
            train (optional): the training series, only needed to compute MASE.
            season: the seasonal lag used for MASE's naive scale (7 = weekly).
    Output: dict with keys: 'mae', 'rmse', 'mape', 'wape', and 'mase' (only if
            `train` is given).

    MAPE divides by each day's actual value, so it is undefined (and here
    excluded) on zero-revenue days, and it overweights low-revenue days.
    WAPE and MASE exist as alternatives that don't have that problem:

    - WAPE (weighted/aggregate MAPE): sum of errors / sum of actuals, computed
      once over the whole window instead of averaged per day. Zero-revenue
      days no longer need special-casing individually.
    - MASE (mean absolute scaled error): this forecast's MAE divided by the
      MAE of a naive (t - season) forecast measured in-sample on `train`.
      Well-defined regardless of zeros in `actual`. < 1 = beats the naive
      baseline, > 1 = worse than it. See Hyndman & Koehler (2006).
    """
    errors = actual - predicted
    mae = np.mean(np.abs(errors))
    mse = np.mean(errors**2)
    rmse = np.sqrt(mse)

    mask = actual != 0
    mape = np.mean(
        np.abs(actual[mask] - predicted[mask]) / actual[mask]
    ) * 100

    wape = np.sum(np.abs(errors)) / np.sum(np.abs(actual)) * 100

    metrics = {"mae": mae, "rmse": rmse, "mape": mape, "wape": wape}

    if train is not None:
        naive_in_sample_errors = (train - train.shift(season)).dropna()
        naive_scale = naive_in_sample_errors.abs().mean()
        metrics["mase"] = mae / naive_scale if naive_scale else np.nan

    return metrics


def fit_sarima(train: pd.Series, order: tuple, seasonal_order: tuple):
    """
    Fit a SARIMA model on the training series.
    Input:  train (history), order=(p,d,q), seasonal_order=(P,D,Q,s).
    Output: the fitted SARIMAXResults object (has .aic, .bic, .forecast(), etc.)
    """

    model = SARIMAX(train, order=order, seasonal_order=seasonal_order)
    fitted = model.fit(disp=False)

    return fitted


def forecast_with_ci(model, steps: int, alpha: float = 0.05) -> pd.DataFrame:
    """
    Generate a forecast with confidence intervals.
    Input:  model (fitted SARIMAXResults), steps (how many days ahead),
            alpha (0.05 = 95% confidence interval).
    Output: a DataFrame with columns: 'forecast', 'lower', 'upper'.
    """

    forecast_result = model.get_forecast(steps=steps) 
    mean_forecast = forecast_result.predicted_mean 
    conf_int = forecast_result.conf_int(alpha=alpha)

    return pd.DataFrame({
        "forecast": mean_forecast,
        "lower": conf_int.iloc[:, 0],   
        "upper": conf_int.iloc[:, 1]
    })




# if __name__ == "__main__":
    
#     df = load_processed()
#     daily = aggregate_daily(df)
#     print(daily.shape)
#     print(daily.isna().sum())
#     print((daily == 0).sum())      
#     print(daily.head())
#     train, test = train_test_split_series(daily)
#     print(train.shape, test.shape)
#     print(train.index.max(), test.index.min())
#     result = check_stationarity(train)
    

#     fig, axes = plt.subplots(2, 1, figsize=(10, 8))
#     plot_acf(train, lags=21, ax=axes[0])
#     plot_pacf(train, lags=21, ax=axes[1])
#     plt.tight_layout()
#     plt.savefig("acf_pacf.png")


#     naive_forecast = seasonal_naive_forecast(train, test)
#     print(naive_forecast.head(17))
#     print(naive_forecast.shape)   # should be (28,), same as test
#     print(train.loc["2011-11-05"])


#     metrics = evaluate_forecast(test, naive_forecast)
#     print(metrics)

#     model = fit_sarima(train, order=(1,1,0), seasonal_order=(1,1,0,7))
#     print(model.aic, model.bic)
#     # print(model.summary())

#     forecast = model.forecast(steps=len(test))
#     metrics2 = evaluate_forecast(test, forecast)
#     print(metrics2)


#     model2 = fit_sarima(train, order=(1,1,1), seasonal_order=(1,1,1,7))
#     print(model2.aic, model2.bic)

#     forecast2 = model2.forecast(steps=len(test))
#     metrics2 = evaluate_forecast(test, forecast2)
#     print(metrics2)

#     model3 = fit_sarima(train, order=(2,1,1), seasonal_order=(1,1,1,7))
#     print(model3.aic, model3.bic)
#     forecast3 = model3.forecast(steps=len(test))
#     print(evaluate_forecast(test, forecast3))


#     final_model = fit_sarima(train, order=(1,1,1), seasonal_order=(1,1,1,7))
#     result = forecast_with_ci(final_model, steps=len(test))
#     print(result.head())
#     print(result.shape)
