
import streamlit as st
import pandas as pd
import numpy as np

from scipy.stats import chisquare
from statsmodels.stats.proportion import (
    proportions_ztest,
    confint_proportions_2indep
)
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


# --------------------------------------------------
# Setting up page
# --------------------------------------------------
st.set_page_config(
    page_title="A/B Testing & Conversion Analyzer",
    layout="wide"
)

st.title("A/B Testing & Conversion Analyzer")
st.write(
    "Analyze experiments, validate data quality, "
    "calculate statistical significance, and support "
    "conversion optimization decisions."
)


# --------------------------------------------------
# 2. CSV upload
# --------------------------------------------------
uploaded = st.file_uploader(
    "Upload your experiment CSV",
    type=["csv"]
)

if uploaded is not None:

    raw_df = pd.read_csv(uploaded)
    df = raw_df.copy()

    st.subheader("Data Quality & Cleaning Log")

    required = {"group", "converted"}

    if not required.issubset(df.columns):
        st.error(
            "CSV must contain 'group' and 'converted' columns."
        )
        st.stop()

    cleaning_log = []

    def record_step(step, before, after):
        cleaning_log.append({
            "Step": step,
            "Rows Before": before,
            "Rows After": after,
            "Rows Removed": before - after
        })

    original_rows = len(df)

    # Normalize group labels
    df["group"] = (
        df["group"]
        .astype("string")
        .str.lower()
        .str.strip()
    )

    # Remove missing required values
    before = len(df)
    df = df.dropna(subset=["group", "converted"]).copy()
    record_step("Remove missing required values", before, len(df))

    # Validate group labels
    before = len(df)
    df = df[
        df["group"].isin(["control", "treatment"])
    ].copy()
    record_step("Validate group labels", before, len(df))

    # Convert and validate conversion values
    before = len(df)
    df["converted"] = pd.to_numeric(
        df["converted"], errors="coerce"
    )
    df = df[df["converted"].isin([0, 1])].copy()
    record_step("Validate conversion values", before, len(df))

    # duplicate
    if "user_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(
            subset="user_id", keep="first"
        ).copy()
        record_step("Remove duplicate users", before, len(df))

    cleaning_log_df = pd.DataFrame(cleaning_log)

    st.dataframe(
        cleaning_log_df,
        use_container_width=True,
        hide_index=True
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Original rows", f"{original_rows:,}")
    m2.metric("Cleaned rows", f"{len(df):,}")
    m3.metric(
        "Rows removed",
        f"{original_rows - len(df):,}"
    )

    # Require both groups
    if not {"control", "treatment"}.issubset(
        set(df["group"].unique())
    ):
        st.error(
            "Both control and treatment groups must contain "
            "valid observations."
        )
        st.stop()

    control = df.loc[
        df["group"] == "control", "converted"
    ]
    treatment = df.loc[
        df["group"] == "treatment", "converted"
    ]

    if len(control) == 0 or len(treatment) == 0:
        st.error("Both groups must contain observations.")
        st.stop()

    # --------------------------------------------------
    # 3. sample ratio mismtach(SRM)
    # --------------------------------------------------
    st.subheader("Sample Ratio Mismatch(SRM) Check")

    expected_control_share = st.number_input(
        "Expected control allocation (%)",
        min_value=1.0,
        max_value=99.0,
        value=50.0,
        step=5.0
    ) / 100

    group_counts = (
        df["group"]
        .value_counts()
        .reindex(["control", "treatment"], fill_value=0)
    )

    observed = group_counts.to_numpy()
    total_users = observed.sum()

    expected = np.array([
        total_users * expected_control_share,
        total_users * (1 - expected_control_share)
    ])

    srm_stat, srm_p = chisquare(
        f_obs=observed,
        f_exp=expected
    )

    srm_c1, srm_c2, srm_c3 = st.columns(3)
    srm_c1.metric("Control users", f"{observed[0]:,}")
    srm_c2.metric("Treatment users", f"{observed[1]:,}")
    srm_c3.metric("SRM p-value", f"{srm_p:.6f}")

    srm_flag = srm_p < 0.001

    if srm_flag:
        st.warning(
            "Possible sample ratio mismatch detected. "
            "Investigate assignment, tracking, and data filtering "
            "before trusting the experiment results."
        )
    else:
        st.success(
            "No statistically significant SRM detected "
            "at the 0.1% threshold."
        )

    # --------------------------------------------------
    # 4. Conversion Analysis
    # --------------------------------------------------
    summary = df.groupby("group")["converted"].agg(
        users="count",
        conversions="sum",
        rate="mean"
    )

    control_rate = control.mean()
    treatment_rate = treatment.mean()

    lift = treatment_rate - control_rate

    relative_lift = (
        lift / control_rate * 100
        if control_rate > 0 else np.nan
    )

    z, p = proportions_ztest(
        [int(treatment.sum()), int(control.sum())],
        [len(treatment), len(control)]
    )

    low, high = confint_proportions_2indep(
        int(treatment.sum()), len(treatment),
        int(control.sum()), len(control),
        method="newcomb",
        compare="diff"
    )

    st.subheader("Experiment Results")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Control conversion", f"{control_rate:.2%}")
    c2.metric("Treatment conversion", f"{treatment_rate:.2%}")
    c3.metric(
        "Relative lift",
        f"{relative_lift:.2f}%"
        if np.isfinite(relative_lift) else "N/A"
    )
    c4.metric("P-value", f"{p:.4f}")

    st.subheader("Group Summary")
    st.dataframe(summary, use_container_width=True)

    st.bar_chart(
        summary["rate"].rename("Conversion rate")
    )

    st.write(
        f"**Absolute lift:** {lift:.2%}"
    )
    st.write(
        f"**95% confidence interval:** "
        f"[{low:.2%}, {high:.2%}]"
    )

    if p < 0.05:
        st.info(
            "The conversion-rate difference is statistically "
            "significant at the 5% level."
        )
    else:
        st.info(
            "The experiment did not establish a statistically "
            "significant conversion-rate difference."
        )

    # --------------------------------------------------
    # 5. Power Calculator
    # --------------------------------------------------
    st.subheader("Statistical Power Calculator")
    st.write(
        "Estimate the sample size needed for a future "
        "two-group conversion experiment."
    )

    pc1, pc2 = st.columns(2)

    with pc1:
        baseline = st.number_input(
            "Baseline conversion rate (%)",
            min_value=0.1,
            max_value=98.0,
            value=10.0,
            step=0.5
        ) / 100

        mde = st.number_input(
            "Minimum detectable effect (percentage points)",
            min_value=0.1,
            max_value=50.0,
            value=2.0,
            step=0.5
        ) / 100

    with pc2:
        alpha = st.selectbox(
            "Significance level",
            [0.01, 0.05, 0.10],
            index=1
        )

        target_power = st.selectbox(
            "Target power",
            [0.70, 0.80, 0.90, 0.95],
            index=1
        )

    target_rate = baseline + mde

    if target_rate >= 1:
        st.error(
            "Baseline conversion plus MDE must be below 100%."
        )
    else:
        effect_size = abs(
            proportion_effectsize(baseline, target_rate)
        )

        power_model = NormalIndPower()

        required_n = power_model.solve_power(
            effect_size=effect_size,
            power=target_power,
            alpha=alpha,
            ratio=1.0,
            alternative="two-sided"
        )

        required_n = int(np.ceil(required_n))

        p1, p2 = st.columns(2)
        p1.metric(
            "Required per group",
            f"{required_n:,}"
        )
        p2.metric(
            "Total required sample",
            f"{2 * required_n:,}"
        )

        st.caption(
            "This is a planning estimate for a two-sided "
            "two-proportion test with equal group sizes."
        )

    # --------------------------------------------------
    # 6. Automated Business Conclusion
    # --------------------------------------------------
    st.subheader("Business Conclusion")

    if srm_flag:
        st.warning(
            "Data quality warning: possible SRM. Investigate "
            "the experiment before making a rollout decision."
        )

    if p < 0.05 and lift > 0:
        conclusion = (
            f"The treatment increased conversion from "
            f"{control_rate:.2%} to {treatment_rate:.2%}, "
            f"an absolute lift of {lift:.2%} and relative lift "
            f"of {relative_lift:.2f}%. The difference is "
            f"statistically significant (p = {p:.4f})."
        )

        recommendation = (
            "Consider a staged rollout only after validating "
            "experiment quality and business guardrail metrics."
        )

    elif p < 0.05 and lift < 0:
        conclusion = (
            f"The treatment decreased conversion from "
            f"{control_rate:.2%} to {treatment_rate:.2%}, "
            f"an absolute change of {lift:.2%}. The difference "
            f"is statistically significant (p = {p:.4f})."
        )

        recommendation = (
            "Do not roll out the treatment as-is. Investigate "
            "the negative effect and its business implications."
        )

    else:
        conclusion = (
            f"Control conversion was {control_rate:.2%}, "
            f"while treatment conversion was {treatment_rate:.2%}. "
            f"The estimated absolute lift was {lift:.2%}, but "
            f"the result was not statistically significant "
            f"(p = {p:.4f}). This does not establish equivalence."
        )

        recommendation = (
            "Review the confidence interval, planned sample size, "
            "and statistical power before deciding whether to "
            "continue testing."
        )

    st.markdown(f"**Findings:** {conclusion}")
    st.markdown(f"**Recommendation:** {recommendation}")

    if srm_flag:
        st.warning(
            "The conclusion is provisional because the SRM "
            "check flagged a potential assignment imbalance."
        )

    st.caption(
        "Interpret results alongside experiment design, "
        "randomization, sample quality, and business guardrails. "
        "Statistical significance alone does not guarantee "
        "business value."
    )

else:
    st.info("Upload your experiment CSV to begin.")
