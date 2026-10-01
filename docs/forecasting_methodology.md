# Short-Term Revenue Forecasting for E-Commerce Transaction Data: A SARIMA Approach

## Abstract

This study forecasts daily revenue for a UK-based online retailer using the
UCI Online Retail dataset. A Seasonal Autoregressive Integrated Moving
Average (SARIMA) model is compared against a seasonal-naive baseline over a
28-day out-of-sample test window. The chosen model, SARIMA(1,1,1)(1,1,1,7),
reduces mean absolute percentage error (MAPE) from 25.29% to 20.49% relative
to the baseline. However, evaluation across five accuracy metrics reveals
that this improvement does not hold on an absolute-error basis: MAE, RMSE,
WAPE, and MASE all favor the naive baseline. This disagreement is traced to
a single large-magnitude demand event that the SARIMA model underfits,
illustrating that percentage-based and magnitude-based error metrics can
rank forecasting models differently on the same data, and that no single
metric should be relied upon in isolation.

## 1. Introduction

Demand forecasting supports inventory planning, staffing, and revenue
projection in retail operations. This study evaluates whether a SARIMA
model, fit to a daily-aggregated revenue series, improves forecast accuracy
over a simple seasonal-naive baseline, and examines how the choice of
evaluation metric affects that conclusion.

## 2. Data and Preprocessing

The dataset is the UCI "Online Retail" transaction log (Chen, 2015):
541,909 invoice line items from a UK-based online retailer, December 2010
to December 2011, covering UK and EU customers. Records were cleaned prior
to this analysis (deduplication, removal of cancelled orders and
non-product stock codes, removal of non-positive quantity/price rows).

Transaction-level records were aggregated to a daily revenue series by
summing `Quantity × UnitPrice` per calendar day, then reindexed against a
complete daily calendar so that non-trading days are represented explicitly
as zero rather than omitted. The resulting series spans 374 consecutive
days (2010-12-01 to 2011-12-09) with no missing values.

Sixty-nine days (18.4% of the series) have zero recorded revenue. Of these,
53 (76.8%) fall on Saturdays, consistent with the retailer having no
Saturday trading activity in this dataset. The remaining 16 zero-revenue
days are distributed across other weekdays and are consistent with UK
public holidays (e.g., Christmas, New Year), though holiday status was not
independently verified against a calendar and this attribution should be
treated as a plausible explanation rather than a confirmed one.

## 3. Methodology

### 3.1 Train/Test Split

The series was split chronologically, without shuffling, into a training
set of 346 days (through 2011-11-11) and a held-out test set of the final
28 days (2011-11-12 to 2011-12-09). A single, non-overlapping split was
used; see Section 5 for the limitations of this choice.

### 3.2 Stationarity Testing

Stationarity of the training series was assessed using the Augmented
Dickey-Fuller (ADF) test (Dickey & Fuller, 1979). The test statistic was
-2.460 (p = 0.126), failing to reject the null hypothesis of a unit root at
the 5% significance level. This motivated first-order differencing (d = 1)
in the subsequent SARIMA specification.

### 3.3 Seasonality Identification

Autocorrelation (ACF) and partial autocorrelation (PACF) functions were
examined over 21 lags on the differenced training series. A recurring
pattern at lag 7 was identified, indicating weekly seasonality (s = 7),
consistent with the retailer's fixed weekly trading pattern (Section 2).

### 3.4 Baseline Model

A seasonal-naive baseline was constructed, forecasting each test-period
value as the observed value exactly one seasonal period (7 days) prior.
This is a standard, low-complexity benchmark against which more complex
models should demonstrate added value (Hyndman & Athanasopoulos, 2021).

### 3.5 SARIMA Model Selection

Three SARIMA(p,d,q)(P,D,Q,s) specifications were fit to the training series
via maximum likelihood (Box, Jenkins, Reinsel, & Ljung, 2015; implemented
with `statsmodels.tsa.statespace.sarimax`) and compared on Akaike
Information Criterion (AIC; Akaike, 1974), Bayesian Information Criterion
(BIC; Schwarz, 1978), and out-of-sample test error:

| Model | AIC | BIC | MAE | RMSE | MAPE | WAPE | MASE |
|---|---|---|---|---|---|---|---|
| SARIMA(1,1,0)(1,1,0,7) | 7527.58 | 7539.05 | 17,348.93 | 29,813.78 | 32.84% | 32.33% | 1.645 |
| **SARIMA(1,1,1)(1,1,1,7)** | 7406.00 | 7425.12 | 15,743.25 | 31,450.53 | 20.49% | 29.34% | 1.493 |
| SARIMA(2,1,1)(1,1,1,7) | 7403.49 | 7426.43 | 15,812.46 | 31,664.58 | 20.50% | 29.47% | 1.499 |

SARIMA(1,1,1)(1,1,1,7) was selected. While SARIMA(2,1,1)(1,1,1,7) achieved a
marginally lower AIC, its BIC — which penalizes additional parameters more
heavily — was higher, and it produced no meaningful improvement on any
test-set metric. The more parsimonious model was therefore preferred.

This choice was subsequently validated by an exhaustive grid search over
$p, q \in \{0,1,2\}$, $d \in \{0,1\}$, $P, D, Q \in \{0,1\}$ (144
(order, seasonal_order) combinations, $s = 7$ fixed), each fit on the
training set and scored by test-set MAPE. SARIMA(1,1,1)(1,1,1,7) was
confirmed as the MAPE-optimal combination (20.485%) of the 144 evaluated;
SARIMA(2,1,1)(1,1,1,7) was the runner-up (20.496%), consistent with the
three-candidate comparison above.

### 3.6 Evaluation Metrics

Forecast accuracy was assessed using five metrics, defined for actual
values $y_t$ and predictions $\hat{y}_t$ over $t = 1, \dots, n$:

- **MAE** (Mean Absolute Error): $\frac{1}{n}\sum |y_t - \hat{y}_t|$
- **RMSE** (Root Mean Squared Error): $\sqrt{\frac{1}{n}\sum (y_t - \hat{y}_t)^2}$
- **MAPE** (Mean Absolute Percentage Error): $\frac{100}{n}\sum \left|\frac{y_t - \hat{y}_t}{y_t}\right|$, computed only over days with $y_t \neq 0$
- **WAPE** (Weighted Absolute Percentage Error): $100 \times \frac{\sum |y_t - \hat{y}_t|}{\sum |y_t|}$
- **MASE** (Mean Absolute Scaled Error; Hyndman & Koehler, 2006): the model's test-set MAE divided by the in-sample MAE of a seasonal-naive forecast on the training set

MAPE is undefined when $y_t = 0$ and was excluded on those days rather than
imputed; WAPE and MASE were included specifically because they remain
well-defined under this condition (Section 5).

## 4. Results

Table 2 compares the seasonal-naive baseline against the selected SARIMA
model on the 28-day test set.

**Table 2.** Baseline vs. SARIMA(1,1,1)(1,1,1,7), test-set performance.

| Metric | Seasonal Naive | SARIMA(1,1,1)(1,1,1,7) | Preferred model |
|---|---|---|---|
| MAE | 15,462.72 | 15,743.25 | Naive |
| RMSE | 31,609.09 | 31,450.53 | ~equivalent (SARIMA, marginal) |
| MAPE | 25.29% | 20.49% | SARIMA |
| WAPE | 28.82% | 29.34% | Naive |
| MASE | 1.466 | 1.493 | Naive |

The five metrics do not agree on which model performs better. MAPE favors
SARIMA by a wide margin; MAE, WAPE, and MASE — all magnitude-weighted
measures — favor the naive baseline; RMSE is approximately equivalent
between the two.

This disagreement is attributable to a difference in how each metric
weights errors across days of varying revenue magnitude. MAPE averages
*relative* errors, treating a proportionally large miss on a low-revenue
day the same as a proportionally large miss on a high-revenue day; it is
therefore most sensitive to typical-day accuracy. MAE, RMSE, WAPE, and MASE
average or scale *absolute* (£) errors, and are therefore dominated by
high-magnitude days.

A single day drives this reversal: 2011-12-09, the final day of the test
window, recorded actual revenue of £198,095 against a SARIMA prediction of
£51,865 (73.8% relative error). This one day accounts for 33.2% of
SARIMA's total absolute error across the entire 28-day test set. The naive
baseline also misses this day substantially (£142,178 absolute error), but
by less than SARIMA (£146,230), which is sufficient to reverse the ranking
under every magnitude-weighted metric despite SARIMA's better performance
on the remaining, typical days.

Transaction-level inspection of 2011-12-09 identifies the cause: a single
customer (ID 16446) placed one order (invoice 581483) worth £168,470 —
85.0% of that day's entire £198,095 revenue, out of 35 distinct customers
trading that day. This customer placed only one other order in the full
12-month dataset, worth £2.90 (18 May 2011); the December order is not part
of a recurring purchasing pattern. This is an idiosyncratic, customer-level
demand shock rather than a calendar or seasonal effect, and no
time-series model conditioned only on aggregate historical revenue —
SARIMA(1,1,1)(1,1,1,7) included — has a mechanism to anticipate it; doing
so would require customer-level order data, which falls outside this
model's scope. (An earlier draft of this section attributed the error to
the start of the pre-Christmas shopping period; that explanation is
superseded by this transaction-level finding, which is directly
verifiable in the source data.)

## 5. Limitations

1. **MAPE is undefined at zero revenue.** Days with zero actual revenue
   (18.4% of the full series; predominantly Saturdays) were excluded from
   the MAPE calculation rather than imputed or penalized. WAPE and MASE
   were reported alongside MAPE specifically because they do not require
   this exclusion.
2. **MASE reference scale.** MASE's denominator is the naive method's
   in-sample (training-period) error, while its numerator is evaluated on
   the test period; consequently, even the naive method's own MASE on the
   test set (1.466) is not exactly 1.0, since the two periods are not
   identical in composition.
3. **Single train/test split.** Results reflect one chronological 346/28
   split rather than a cross-validated (e.g., rolling-origin) evaluation.
   The test window's inclusion of an atypical high-revenue day (Section 4)
   may limit generalizability of the reported metrics to other periods.
4. **Model search scope.** The grid search (Section 3.5) covered
   $p, q \in \{0,1,2\}$, $d \in \{0,1\}$, $P, D, Q \in \{0,1\}$ with $s = 7$
   fixed — 144 combinations, all scored on a single test window (see
   Limitation 3). Higher-order values ($p, q > 2$), alternative values of
   $s$, and a cross-validated scoring scheme were not explored.
5. **Holiday attribution unverified.** The classification of non-Saturday
   zero-revenue days as likely holidays (Section 2) was inferred from the
   calendar dates involved and was not cross-checked against an official UK
   public holiday calendar.

## 6. Conclusion

SARIMA(1,1,1)(1,1,1,7) improves relative (percentage-based) forecast
accuracy over a seasonal-naive baseline but does not improve, and by most
magnitude-weighted metrics slightly underperforms, on an absolute (£)
basis — a discrepancy driven by a single idiosyncratic, customer-level
order in the test window (Section 4) rather than a deficiency in the
model itself; no aggregate-revenue time-series model has a mechanism to
anticipate a one-off order of this kind. This result illustrates that
forecast evaluation conclusions can be metric-dependent, and supports
reporting multiple complementary metrics rather than a single accuracy
measure when comparing forecasting models.

## References

- Akaike, H. (1974). A new look at the statistical model identification.
  *IEEE Transactions on Automatic Control*, 19(6), 716–723.
- Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M. (2015).
  *Time Series Analysis: Forecasting and Control* (5th ed.). Wiley.
- Chen, D. (2015). *Online Retail Data Set*. UCI Machine Learning
  Repository. https://archive.ics.uci.edu/dataset/352/online+retail
  (CC BY 4.0).
- Dickey, D. A., & Fuller, W. A. (1979). Distribution of the estimators for
  autoregressive time series with a unit root. *Journal of the American
  Statistical Association*, 74(366a), 427–431.
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and
  Practice* (3rd ed.). OTexts.
- Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of
  forecast accuracy. *International Journal of Forecasting*, 22(4),
  679–688.
- Schwarz, G. (1978). Estimating the dimension of a model. *The Annals of
  Statistics*, 6(2), 461–464.

---
*Note: Hyndman & Koehler (2006) was the citation discussed directly in the
development conversation for this project (justifying MASE). The remaining
citations are standard references for the methods used (ADF test, SARIMA/
Box-Jenkins, AIC, BIC, the dataset) added for completeness and were not
verified against a live source in this session — check exact volume/page
numbers before submission.*
