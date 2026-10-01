import streamlit as st
from src.data_loader import load_processed
from src.sampling import (
    compute_rfm_tiers,
    proportional_allocation,
    neyman_allocation,
    draw_stratified_sample,
    validate_representativeness,
)

st.title("Stratified Sampling Tool")
st.caption(
    "Draw a statistically representative sample from the UCI Online Retail "
    "dataset for research use."
)

df = load_processed()

# --- Strata choice first: it determines the working population, which the
# sample-size limit below must respect. ---
col1, col2 = st.columns(2)
with col1:
    strata_choice = st.selectbox("Stratify by", ["Country", "Customer Value Tier (RFM)"])
with col2:
    method = st.selectbox("Allocation method", ["Proportional", "Neyman (optimal)"])

if strata_choice == "Country":
    strata_col = "Country"
    working_df = df
else:
    rfm = compute_rfm_tiers(
        df, customer_col="CustomerID", date_col="InvoiceDate",
        invoice_col="InvoiceNo", revenue_col="Revenue",
    )
    working_df = df.merge(rfm[["tier"]], left_on="CustomerID", right_index=True, how="inner")
    strata_col = "tier"

    excluded_rows = len(df) - len(working_df)
    excluded_revenue = df.loc[df["CustomerID"].isna(), "Revenue"].sum()
    st.warning(
        f"RFM tiers require a customer ID: **{excluded_rows:,} rows "
        f"({excluded_rows / len(df):.1%})** with no CustomerID — "
        f"£{excluded_revenue:,.0f} of revenue — are excluded from this "
        "population. Use Country stratification to sample from the full dataset."
    )

st.info(
    f"Population: **{len(working_df):,}** rows across "
    f"**{working_df[strata_col].nunique()}** strata."
)

sample_size = st.number_input(
    "Sample size", min_value=50, max_value=len(working_df), value=min(1000, len(working_df)), step=50
)

if method == "Neyman (optimal)":
    st.caption(
        "Neyman allocation over-samples high-variance strata to minimize the "
        "error of an estimated population mean/total — it does **not** aim to "
        "match the population's category mix. The representativeness check "
        "below is expected to fail (p ≤ 0.05) for this method; that is not an error."
    )

# --- Allocate & sample ---
if st.button("Draw Sample", type="primary"):
    strata_sizes = working_df[strata_col].value_counts()

    if method == "Proportional":
        allocation = proportional_allocation(strata_sizes, sample_size)
    else:
        allocation = neyman_allocation(
            working_df, strata_col, value_col="Revenue", total_sample_size=sample_size
        )

    sample_df = draw_stratified_sample(working_df, strata_col, allocation)
    validation = validate_representativeness(working_df, sample_df, strata_col)

    st.session_state["sample_df"] = sample_df
    st.session_state["validation"] = validation
    st.session_state["sample_method"] = method

# --- Results ---
if "sample_df" in st.session_state:
    sample_df = st.session_state["sample_df"]
    validation = st.session_state["validation"]
    sample_method = st.session_state["sample_method"]

    st.subheader("Sample Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Sample Size", f"{len(sample_df):,}")
    c2.metric("Chi-square p-value", f"{validation['p_value']:.4f}")
    if sample_method == "Neyman (optimal)":
        c3.metric(
            "Representative?", "N/A by design",
            help="Neyman allocation optimizes estimation efficiency, not category "
                 "match — see the caption above. A low p-value here is expected.",
        )
    else:
        c3.metric(
            "Representative?",
            "✅ Yes" if validation["is_representative"] else "⚠️ No",
            help="p > 0.05 means we fail to reject that the sample's stratum "
                 "distribution matches the population's.",
        )

    st.subheader("Population vs. Sample Distribution")
    st.dataframe(validation["comparison_table"], width="stretch")
    st.bar_chart(validation["comparison_table"][["population_pct", "sample_pct"]])

    st.download_button(
        "📥 Download Sample (CSV)",
        sample_df.to_csv(index=False).encode("utf-8"),
        "stratified_sample.csv",
        "text/csv",
    )
