# Known Limitations & Defense Notes

Each entry: what the issue is, why it happens, how it's handled in the app,
and a ready answer for a reviewer/defense question. Copy directly into the
paper's Limitations section as needed; add a new entry (using the template
at the bottom) whenever a new issue is found rather than letting it sit
undocumented.

---

## 1. Guest Checkout Exclusion in RFM Stratification

**Issue:** 131,426 rows (25.1% of transactions, £1,511,042 of revenue, 14.7%
of total revenue) are excluded from RFM-based stratified sampling because
they lack a CustomerID (guest/anonymous checkouts).

**Why it happens:** RFM (Recency, Frequency, Monetary) scoring requires
customer-level aggregation — recency and frequency are undefined without a
customer identity to group by.

**How handled:** These rows are automatically excluded before RFM tiering
(see `compute_rfm_tiers()` in `src/sampling.py`; the exclusion happens via
the inner join in `views/stratified_sampling.py`, not inside the function
itself). The app shows the exact excluded row count and revenue in a
warning box whenever RFM stratification is selected. Country-based
stratification remains available as a full-coverage alternative that
includes guest transactions.

**Defense answer:** "RFM-tier sampling necessarily excludes anonymous
transactions since customer identity is required for the methodology. This
is disclosed transparently in-app with the exact figures, and we offer
Country-based stratification as a complete-coverage alternative when guest
transactions must be included."

See `docs/sampling_methodology.md` §5.1 for the full writeup.

---

## 2. MAPE vs MAE Disagreement in SARIMA Forecast Evaluation

**Issue:** Standard MAPE favors SARIMA (20.49%) over the seasonal-naive
baseline (25.29%), but MAE (£-weighted) slightly favors the naive baseline
(£15,463 vs £15,743) on the same test set.

**Why it happens:** A single transaction dominates both metrics in opposite
directions. On 2011-12-09, one customer (ID 16446) placed a single order
(invoice 581483) worth £168,470 — 85% of that day's entire £198,095
revenue. That customer placed only one other order in the whole dataset,
worth £2.90 — this is a one-off, idiosyncratic order, not a recurring
wholesale relationship. SARIMA misses this day by more (£146,230) than the
naive baseline does (£142,178), which is enough on its own to flip the
£-weighted metrics (MAE, RMSE, WAPE, MASE) in naive's favor, while MAPE —
which weights every day equally in percentage terms regardless of revenue
size — is comparatively insensitive to this one day and still favors
SARIMA.

**How handled:** Added WAPE and MASE alongside MAE/RMSE/MAPE
(`evaluate_forecast()` in `src/forecasting.py`), plus Median APE and
Trimmed MAPE (90th percentile) on the Methodology page, to show accuracy
on a "typical" day independent of this one transaction. The transaction-
level cause is shown directly in the Forecast Error Breakdown table.

**Defense answer:** "We report five accuracy metrics, not one, because
retail transaction data contains customer-driven, heavy-tailed outliers
that a single point-estimate metric can distort in either direction. The
specific outlier transaction is identified and quantified in-app, and
reported honestly rather than smoothed over."

See `docs/forecasting_methodology.md` §6 and §4 for the full writeup.

---

## 3. Stratified-Sampling Variance Estimates Are Unstable Across Runs

**Issue:** When comparing Proportional vs. Neyman allocation on estimation
efficiency (standard error of an estimated population total), the
*reduction* Neyman achieves is consistent (3.1%–13.9% across 5 random
seeds, always positive), but the *absolute* standard error values vary by
roughly 4x between seeds (e.g. £517,770 to £2,125,375 for proportional
allocation at n=1,000).

**Why it happens:** Country is a highly imbalanced stratification variable
— the UK dominates the population, so every other country stratum gets a
very small sample size at n=1,000. The per-stratum sample variance used in
both the Neyman weighting and the SE formula is estimated from that small
sample, making the estimate itself noisy run-to-run.

**How handled:** The comparison was repeated across 5 random seeds rather
than reported from a single run, and the instability is disclosed
explicitly as a limitation rather than presenting one seed's number as
definitive.

**Defense answer:** "The direction of the result — Neyman reduces
estimator variance — is robust across seeds; the magnitude is not, because
most country strata are too small to estimate their internal variance
precisely at this sample size. A larger total sample, or restricting the
comparison to well-populated strata, would stabilize the magnitude."

See `docs/sampling_methodology.md` §4.2 and §5.2 for the full writeup.

---

## Template for future entries

```markdown
## N. [Short, specific title]

**Issue:** [What is observed — with exact numbers, not "some" or "many"]

**Why it happens:** [The actual mechanism, verified against the data —
not a plausible-sounding guess]

**How handled:** [What the app/code does about it, with the function or
file name]

**Defense answer:** [A one-paragraph, reviewer-ready response]
```
