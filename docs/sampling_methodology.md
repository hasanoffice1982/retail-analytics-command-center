# Stratified Sampling of the Transaction-Level Dataset

## 1. Objective

Draw a statistically representative subset of the cleaned transaction-level
dataset (522,709 rows), suitable for research use where full-dataset
analysis is unnecessary or for demonstrating stratified sampling technique
as a methodology in its own right.

## 2. Stratification Variable

Two stratification variables are implemented and compared:

- **Country.** The simpler option, but naive on its own: the United Kingdom
  accounts for the large majority of transactions, so country-based strata
  are highly imbalanced by construction.
- **Customer Value Tier (RFM).** Customers are scored on Recency (days
  since last purchase), Frequency (distinct invoices), and Monetary value
  (total revenue), each quantile-binned into 3 levels and summed into an
  RFM score, which is then quantile-binned again into three tiers: Low,
  Medium, High Value. This targets heterogeneous subgroups by purchasing
  behavior rather than geography, which is the more defensible stratifying
  variable for demonstrating why stratification matters — the subgroups
  genuinely differ in revenue variance, which Section 4 makes directly
  relevant to allocation method choice.

## 3. Allocation Methods Compared

**Proportional allocation** draws from each stratum in proportion to its
share of the population — the conventional default, which reproduces the
population's categorical mix by construction.

**Neyman (optimal) allocation** instead allocates more sample to strata
with higher internal variance in the value of interest (here, `Revenue`),
which minimizes the variance of an estimated population total/mean for
that variable. It does not aim to reproduce the population's categorical
mix, and is not expected to.

## 4. Results

### 4.1 Representativeness (chi-square goodness-of-fit)

Both methods were run on Country strata, n=1,000, against the full
522,709-row population:

| Method | Chi-square p-value | Representative (p > 0.05)? |
|---|---|---|
| Proportional | 1.0000 | Yes |
| Neyman | 0.0019 | No — **expected**, not a defect |

Neyman's low p-value is the direct, expected consequence of deliberately
over-sampling high-variance strata rather than matching the population's
mix — see Section 4.2 for what Neyman is actually optimizing instead.

### 4.2 Estimation efficiency (standard error of estimated total revenue)

The point of Neyman allocation is not categorical representativeness but a
lower-variance estimate of a population total. Using the classical
stratified-sampling variance estimator,
$\widehat{\mathrm{Var}}(\hat{T}) = \sum_h N_h^2\left(1 - \frac{n_h}{N_h}\right)\frac{s_h^2}{n_h}$,
the standard error of the estimated total revenue was computed for both
methods at n=1,000, repeated across 5 random seeds:

| Seed | Proportional SE | Neyman SE | Reduction |
|---|---|---|---|
| 1 | £899,067 | £867,125 | 7.0% |
| 2 | £1,803,542 | £1,740,321 | 6.9% |
| 3 | £2,125,375 | £1,972,647 | 13.9% |
| 42 | £517,770 | £482,576 | 13.1% |
| 99 | £1,323,510 | £1,302,890 | 3.1% |

Neyman allocation reduced the standard error in every seed tested (range
3.1%–13.9%, mean 8.8%) — consistent with theory, and never worse than
proportional. The absolute SE values vary substantially by seed because
many country strata (all but the UK) receive very few sampled units,
making the per-stratum sample variance itself a noisy estimate — this is
a limitation of the comparison, not of either allocation method (Section 5).

**Recommendation:** proportional allocation is used as the default in the
tool, since it already achieves excellent representativeness (p≈1.0) and
is the more interpretable choice for general use. Neyman is offered
alongside it specifically to demonstrate the representativeness/efficiency
trade-off, not as a replacement default.

## 5. Limitations

1. **RFM-tier stratification excludes 25.1% of the dataset.** 131,426 of
   522,709 rows (£1,511,042 of revenue, 14.7% of total) have no
   `CustomerID` and cannot be assigned an RFM tier — these are excluded
   from the sampling population whenever RFM stratification is selected.
   This is disclosed to the user in-app (a warning box with the exact
   figures) but is a real constraint on what the RFM-stratified sample can
   claim to represent: it represents *identified customers only*, not the
   full transaction population. Country stratification does not have this
   limitation, since `Country` is populated on every row.
2. **Variance estimates are themselves noisy at this sample size.** The
   per-stratum sample variance used in both the Neyman allocation weights
   and the SE comparison (Section 4.2) is estimated from a small per-stratum
   sample for every country except the UK, which can make the estimate
   unstable run-to-run (seed-to-seed SE ranged over 4x in testing). A
   larger total sample size, or restricting the comparison to a few
   well-populated strata, would give a more stable efficiency estimate.
3. **RFM tier boundaries are quantile-based, not behaviorally validated.**
   Tiers are defined by splitting recency/frequency/monetary scores into
   equal-sized bins (with ties handled via `duplicates="drop"`), not by an
   independently validated customer segmentation — the resulting tier
   sizes are consequently uneven (Low 1,927 / Medium 1,124 / High 1,283
   customers) rather than exactly equal thirds.
