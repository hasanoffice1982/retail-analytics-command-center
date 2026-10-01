"""Stratified sampling utilities for representative subset extraction."""

from __future__ import annotations

import pandas as pd
from scipy import stats


def compute_rfm_tiers(
    df: pd.DataFrame,
    customer_col: str,
    date_col: str,
    invoice_col: str,
    revenue_col: str,
    n_tiers: int = 3,
) -> pd.DataFrame:
    """
    Compute RFM (Recency, Frequency, Monetary) scores per customer and
    bucket them into value tiers (e.g. Low/Medium/High).

    Rows with a missing `customer_col` are dropped automatically by the
    groupby (pandas excludes NaN keys) — callers must account for this
    when joining the result back to the transaction-level data, since
    customer-less transactions (guest-style rows) can't be given a tier.

    Returns a DataFrame indexed by customer with columns:
    recency, frequency, monetary, rfm_score, tier
    """
    snapshot_date = df[date_col].max() + pd.Timedelta(days=1)

    rfm = df.groupby(customer_col).agg(
        recency=(date_col, lambda x: (snapshot_date - x.max()).days),
        frequency=(invoice_col, "nunique"),
        monetary=(revenue_col, "sum"),
    )

    # Edge case: customers with zero/negative monetary (returns-only)
    # get dropped from tiering — they can't be ranked meaningfully
    rfm = rfm[rfm["monetary"] > 0].copy()

    # Quantile-based scoring (handles skewed retail distributions better than raw cuts)
    labels = list(range(1, n_tiers + 1))
    rfm["r_score"] = pd.qcut(rfm["recency"], n_tiers, labels=labels[::-1], duplicates="drop")
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), n_tiers, labels=labels, duplicates="drop"
    )
    rfm["m_score"] = pd.qcut(rfm["monetary"], n_tiers, labels=labels, duplicates="drop")

    rfm["rfm_score"] = (
        rfm["r_score"].astype(int) + rfm["f_score"].astype(int) + rfm["m_score"].astype(int)
    )

    tier_labels = ["Low Value", "Medium Value", "High Value"]
    rfm["tier"] = pd.qcut(rfm["rfm_score"], len(tier_labels), labels=tier_labels, duplicates="drop")

    return rfm


def proportional_allocation(strata_sizes: pd.Series, total_sample_size: int) -> pd.Series:
    """Allocate sample size per stratum proportional to its population share."""
    population_total = strata_sizes.sum()
    allocation = (strata_sizes / population_total * total_sample_size).round().astype(int)

    # Edge case: rounding can make allocation not sum exactly to total_sample_size.
    # Fix by adjusting the largest stratum.
    diff = total_sample_size - allocation.sum()
    if diff != 0:
        largest_stratum = allocation.idxmax()
        allocation[largest_stratum] += diff

    # Edge case: never allocate more than the stratum's population. This can
    # pull the total back below total_sample_size if a stratum is small —
    # draw_stratified_sample() and the caller's reported sample size reflect
    # the true achievable count, not the requested one.
    allocation = allocation.clip(upper=strata_sizes)
    return allocation


def neyman_allocation(
    df: pd.DataFrame, strata_col: str, value_col: str, total_sample_size: int
) -> pd.Series:
    """
    Neyman optimal allocation — allocates more sample to strata with higher
    internal variance in `value_col`, minimizing the variance of an estimated
    population mean/total for that column.

    This optimizes for estimation efficiency, not for the sample's categorical
    mix matching the population's — a stratified sample built this way is
    expected to look less like the population than a proportional one. See
    validate_representativeness()'s docstring for why its chi-square check
    is the wrong success criterion for this allocation method.
    """
    stats_by_stratum = df.groupby(strata_col)[value_col].agg(["count", "std"]).fillna(0)
    weight = stats_by_stratum["count"] * stats_by_stratum["std"]

    if weight.sum() == 0:
        # Edge case: zero variance everywhere — fall back to proportional
        return proportional_allocation(stats_by_stratum["count"], total_sample_size)

    allocation = (weight / weight.sum() * total_sample_size).round().astype(int)
    diff = total_sample_size - allocation.sum()
    if diff != 0:
        allocation[allocation.idxmax()] += diff

    allocation = allocation.clip(upper=stats_by_stratum["count"].astype(int))
    return allocation


def draw_stratified_sample(
    df: pd.DataFrame, strata_col: str, allocation: pd.Series, random_state: int = 42
) -> pd.DataFrame:
    """Draw the actual sample rows given a per-stratum allocation plan."""
    samples = []
    for stratum, n in allocation.items():
        stratum_df = df[df[strata_col] == stratum]
        n_available = len(stratum_df)
        # Edge case: can't sample more than available (shouldn't happen post-clip, but safe)
        n_draw = min(n, n_available)
        if n_draw > 0:
            samples.append(stratum_df.sample(n=n_draw, random_state=random_state))
    return pd.concat(samples, ignore_index=True) if samples else pd.DataFrame(columns=df.columns)


def validate_representativeness(population: pd.DataFrame, sample: pd.DataFrame, strata_col: str) -> dict:
    """
    Chi-square goodness-of-fit test: does the sample's stratum distribution
    match the population's? Returns test stats + per-stratum comparison table.

    Only a meaningful success criterion for a *proportional* allocation. A
    Neyman-allocated sample is deliberately skewed toward high-variance
    strata, so it is expected to fail this test even when it is doing
    exactly what it was built to do (minimize estimator variance, not
    mirror the population's mix) — callers must not present "Neyman + not
    representative" as an error.
    """
    pop_dist = population[strata_col].value_counts(normalize=True).sort_index()
    sample_counts = sample[strata_col].value_counts().sort_index()

    # Align indices (a stratum might be missing from sample if allocation was 0)
    sample_counts = sample_counts.reindex(pop_dist.index, fill_value=0)
    expected_counts = pop_dist * len(sample)

    # Edge case: chi-square requires expected count > 0 in every category
    valid_mask = expected_counts > 0
    chi2_stat, p_value = stats.chisquare(
        f_obs=sample_counts[valid_mask], f_exp=expected_counts[valid_mask]
    )

    comparison = pd.DataFrame(
        {
            "population_pct": (pop_dist * 100).round(2),
            "sample_pct": (sample[strata_col].value_counts(normalize=True) * 100).round(2),
        }
    ).fillna(0)
    comparison["difference_pp"] = (comparison["sample_pct"] - comparison["population_pct"]).round(2)

    return {
        "chi2_statistic": chi2_stat,
        "p_value": p_value,
        "is_representative": p_value > 0.05,  # fail to reject H0: distributions match
        "comparison_table": comparison,
    }
