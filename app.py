"""
app.py — A/B Testing Decision Engine | Fintech Loan CTA Experiment
Run with: streamlit run app.py
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import streamlit as st

from modules.sample_size import calculate_sample_size, sample_size_sensitivity_table
from modules.simulator import simulate_ab_test, get_summary_stats
from modules.stats_engine import full_analysis
from modules.business_impact import revenue_impact, break_even_analysis, go_no_go_recommendation

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="A/B Test Engine — Fintech Loan CTA",
    page_icon="📊",
    layout="wide",
)

# ─────────────────────────────────────────────
# Sidebar — all inputs
# ─────────────────────────────────────────────
st.sidebar.title("⚙️ Experiment Parameters")

st.sidebar.markdown("### Test Design")
baseline_conversion = st.sidebar.slider(
    "Baseline Conversion Rate",
    min_value=0.01, max_value=0.15, value=0.042, step=0.001,
    format="%.3f",
    help="Current CTA click-to-apply rate (e.g. 0.042 = 4.2%)",
)
mde = st.sidebar.slider(
    "Minimum Detectable Effect (Relative)",
    min_value=0.05, max_value=0.50, value=0.20, step=0.01,
    format="%.2f",
    help="Smallest relative lift worth detecting (e.g. 0.20 = 20% relative improvement)",
)
alpha = st.sidebar.selectbox(
    "Significance Level (α)",
    options=[0.01, 0.05, 0.10],
    index=1,
    help="Probability of a false positive (Type I error)",
)
power = st.sidebar.selectbox(
    "Statistical Power (1-β)",
    options=[0.70, 0.80, 0.90],
    index=1,
    help="Probability of detecting a real effect (1 - Type II error)",
)
daily_traffic = st.sidebar.number_input(
    "Daily Users (both groups)",
    min_value=100, max_value=500_000, value=3_334, step=100,
    help="Total daily users split across control and treatment",
)

st.sidebar.markdown("### Business Assumptions")
n_monthly_users = st.sidebar.number_input(
    "Monthly Users Post-Launch",
    min_value=1_000, max_value=5_000_000, value=100_000, step=1_000,
    help="Total users who will see the CTA after full rollout",
)
revenue_per_conversion = st.sidebar.number_input(
    "Revenue per Conversion (₹)",
    min_value=100, max_value=50_000, value=1_500, step=100,
    help="Loan processing fee per disbursed loan (not the loan principal)",
)
implementation_cost = st.sidebar.number_input(
    "Implementation Cost (₹)",
    min_value=0, max_value=10_000_000, value=200_000, step=10_000,
    help="One-time engineering + design cost to ship the new CTA",
)

st.sidebar.markdown("### Simulation Controls")
true_lift = st.sidebar.slider(
    "True Lift in Simulation (Relative)",
    min_value=-0.20, max_value=0.50, value=0.18, step=0.01,
    format="%.2f",
    help="The 'ground truth' lift baked into simulated data. Vary this to test sensitivity.",
)
seed = st.sidebar.number_input("Random Seed", min_value=0, max_value=9999, value=42, step=1)

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.title("📊 A/B Test Decision Engine")
st.markdown(
    """
**Scenario:** A fintech lending app is testing a redesigned loan offer CTA button.
The hypothesis is that a more prominent, benefit-led CTA will increase the loan
application initiation rate among eligible users.

This tool walks through the full experiment lifecycle: **sample size planning →
data simulation → statistical inference → business decision**.
"""
)
st.divider()

# ─────────────────────────────────────────────
# SECTION 1 — Sample Size Planning
# ─────────────────────────────────────────────
st.header("1. Sample Size Planning")
st.markdown(
    "Before running any experiment, you need to know how many users are required to detect "
    "your minimum effect size with the chosen power and significance level."
)

ss = calculate_sample_size(
    baseline_conversion=baseline_conversion,
    mde=mde,
    alpha=alpha,
    power=power,
    daily_traffic=daily_traffic,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("N per Group", f"{ss['n_per_group']:,}")
col2.metric("Total Sample", f"{ss['total_n']:,}")
col3.metric("Est. Duration", f"{ss['estimated_days']} days")
col4.metric("Treatment Rate (Expected)", f"{ss['treatment_rate']:.2%}")

st.markdown("#### Sensitivity Table — How MDE Changes Sample Size Requirements")
sensitivity_df = sample_size_sensitivity_table(
    baseline_conversion=baseline_conversion,
    mde_range=[0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50],
    alpha=alpha,
    power=power,
    daily_traffic=daily_traffic,
)
st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)

with st.expander("How to read this table"):
    st.markdown(
        """
- **MDE (Relative)**: The smallest *relative* improvement you want to detect.
  A 20% MDE on a 4.2% baseline means you want to catch lifts down to 5.04%.
- **Larger MDE → Smaller sample needed**: If you only care about big wins, you need fewer users.
- **Trade-off**: A small MDE requires a long test window, increasing the risk of
  contamination (seasonality, external events).
- **Practical rule of thumb**: Choose the MDE that represents the smallest lift
  that would actually change your shipping decision.
"""
    )

st.divider()

# ─────────────────────────────────────────────
# SECTION 2 — Simulation + Statistical Results
# ─────────────────────────────────────────────
st.header("2. Simulate & Analyse")
st.markdown(
    f"The simulation generates synthetic user data with **control rate = {baseline_conversion:.2%}** "
    f"and **treatment rate = {baseline_conversion * (1 + true_lift):.2%}** (true lift = {true_lift:.0%} relative). "
    "Click the button to run."
)

run_button = st.button("▶ Run Simulation", type="primary")

if run_button:
    treatment_conversion = baseline_conversion * (1 + true_lift)
    df = simulate_ab_test(
        n_control=ss["n_per_group"],
        n_treatment=ss["n_per_group"],
        control_conversion=baseline_conversion,
        treatment_conversion=max(0.0, treatment_conversion),
        revenue_per_conversion=float(revenue_per_conversion),
        seed=int(seed),
    )
    summary = get_summary_stats(df)
    results = full_analysis(summary, alpha=alpha)

    # Persist in session state
    st.session_state["df"] = df
    st.session_state["summary"] = summary
    st.session_state["results"] = results

if "results" in st.session_state:
    summary = st.session_state["summary"]
    results = st.session_state["results"]

    # ── Statistical results ──
    ctrl = summary["control"]
    trt = summary["treatment"]

    st.markdown("### Observed Conversion Rates")
    col_chart, col_stats = st.columns([1.2, 1])

    with col_chart:
        fig, ax = plt.subplots(figsize=(6, 4))
        groups = ["Control", "Treatment"]
        rates = [ctrl["rate"], trt["rate"]]
        ci_lower = [results["control_ci"][0], results["treatment_ci"][0]]
        ci_upper = [results["control_ci"][1], results["treatment_ci"][1]]
        errors = [
            [r - lo for r, lo in zip(rates, ci_lower)],
            [hi - r for r, hi in zip(rates, ci_upper)],
        ]
        colors = ["#4C72B0", "#DD8452"]
        bars = ax.bar(groups, rates, color=colors, width=0.4, zorder=2)
        ax.errorbar(
            groups, rates, yerr=errors,
            fmt="none", color="black", capsize=6, linewidth=1.5, zorder=3,
        )
        ax.set_ylabel("Conversion Rate")
        ax.set_title("Conversion Rate by Group\n(95% Wilson CI)", fontsize=11)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1%}"))
        ax.set_ylim(0, max(rates) * 1.5)
        ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
        for bar, rate in zip(bars, rates):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(rates) * 0.04,
                f"{rate:.2%}", ha="center", va="bottom", fontsize=10, fontweight="bold",
            )
        st.pyplot(fig)
        plt.close(fig)

    with col_stats:
        st.markdown("**Group Summary**")
        summary_table = pd.DataFrame(
            {
                "Group": ["Control", "Treatment"],
                "Users": [f"{ctrl['n']:,}", f"{trt['n']:,}"],
                "Conversions": [ctrl["conversions"], trt["conversions"]],
                "Rate": [f"{ctrl['rate']:.2%}", f"{trt['rate']:.2%}"],
                "95% CI": [
                    f"[{results['control_ci'][0]:.2%}, {results['control_ci'][1]:.2%}]",
                    f"[{results['treatment_ci'][0]:.2%}, {results['treatment_ci'][1]:.2%}]",
                ],
            }
        )
        st.dataframe(summary_table, use_container_width=True, hide_index=True)

        st.markdown("**Statistical Tests**")
        zt = results["z_test"]
        ct = results["chi2_test"]
        stats_table = pd.DataFrame(
            {
                "Test": ["Z-test (proportions)", "Chi-square"],
                "Statistic": [f"{zt['z_stat']:.4f}", f"{ct['chi2_stat']:.4f}"],
                "p-value": [f"{zt['p_value']:.6f}", f"{ct['p_value']:.6f}"],
                "Significant": ["Yes ✅" if zt["significant"] else "No ❌", "Yes ✅" if ct["significant"] else "No ❌"],
            }
        )
        st.dataframe(stats_table, use_container_width=True, hide_index=True)

        st.markdown("**Lift Metrics**")
        m1, m2 = st.columns(2)
        lift_color = "normal" if results["relative_lift"] >= 0 else "inverse"
        m1.metric("Relative Lift", f"{results['relative_lift']:.1%}", delta=None)
        m2.metric(
            "Absolute Lift (pp)",
            f"{results['absolute_lift'] * 100:.2f} pp",
        )

    # ── Significance verdict ──
    if results["significant"]:
        st.success(
            f"✅ **Statistically significant** at α={alpha}: p={results['p_value']:.6f}. "
            f"The treatment group shows a **{results['relative_lift']:.1%} relative lift**. "
            "This result is unlikely to be due to chance alone."
        )
    else:
        st.error(
            f"❌ **Not statistically significant** at α={alpha}: p={results['p_value']:.6f}. "
            "Cannot confidently attribute the observed difference to the new CTA. "
            "Consider running longer or revising the hypothesis."
        )

    with st.expander("Why both z-test and chi-square?"):
        st.markdown(
            """
For a 2×2 contingency table with a two-sided alternative,
the chi-square test statistic equals the z-test statistic squared: **χ² = z²**.
Both tests are included here to show equivalence — not because two tests
are needed to reach a conclusion. In practice, use the z-test when you need
a directional result (one-tailed) and want a signed test statistic.
The z-test p-value and the chi-square p-value should match to within rounding error.
"""
        )

    st.divider()

    # ─────────────────────────────────────────────
    # SECTION 3 — Business Impact + Go/No-Go
    # ─────────────────────────────────────────────
    st.header("3. Business Impact & Go/No-Go Decision")

    impact = revenue_impact(
        n_monthly_users=int(n_monthly_users),
        control_rate=ctrl["rate"],
        treatment_rate=trt["rate"],
        revenue_per_conversion=float(revenue_per_conversion),
    )
    breakeven = break_even_analysis(
        implementation_cost=float(implementation_cost),
        incremental_revenue_monthly=impact["incremental_revenue_monthly"],
    )
    rec = go_no_go_recommendation(
        p_value=results["p_value"],
        rel_lift=results["relative_lift"],
        break_even_months=breakeven["break_even_months"],
        alpha=alpha,
    )

    # Revenue impact table
    st.markdown("### Revenue Impact (Post-Rollout Projections)")
    st.caption(
        f"Assumptions: {n_monthly_users:,} monthly users, ₹{revenue_per_conversion:,} revenue per conversion, "
        f"one-time implementation cost ₹{implementation_cost:,}. "
        "Conservative = 80% of point estimate; Optimistic = 120%."
    )

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric(
        "Monthly Lift (Point)",
        f"₹{impact['incremental_revenue_monthly']:,.0f}",
        delta=f"+{impact['incremental_conversions_monthly']:.0f} conversions/mo",
    )
    col_b.metric("Monthly Lift (Conservative)", f"₹{impact['conservative_revenue']:,.0f}")
    col_c.metric("Monthly Lift (Optimistic)", f"₹{impact['optimistic_revenue']:,.0f}")
    col_d.metric("Annual Impact (Point)", f"₹{impact['incremental_revenue_annual']:,.0f}")

    # Break-even chart
    st.markdown("### Break-Even Analysis")
    col_be, col_roi = st.columns([1.5, 1])

    with col_be:
        if breakeven["break_even_months"] != float("inf") and breakeven["break_even_months"] <= 36:
            months = np.arange(0, 25)
            cumulative_revenue = months * impact["incremental_revenue_monthly"]
            be_month = breakeven["break_even_months"]

            fig2, ax2 = plt.subplots(figsize=(6, 3.5))
            ax2.plot(months, cumulative_revenue, color="#2ecc71", linewidth=2, label="Cumulative Revenue")
            ax2.axhline(implementation_cost, color="#e74c3c", linestyle="--", linewidth=1.5, label="Implementation Cost")
            ax2.axvline(be_month, color="#f39c12", linestyle=":", linewidth=1.5, label=f"Break-even ({be_month:.1f} mo)")
            ax2.fill_between(
                months, implementation_cost, cumulative_revenue,
                where=(cumulative_revenue >= implementation_cost),
                alpha=0.15, color="#2ecc71",
            )
            ax2.set_xlabel("Months Post-Launch")
            ax2.set_ylabel("Cumulative Revenue (₹)")
            ax2.set_title("Break-Even Timeline", fontsize=11)
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"₹{y:,.0f}"))
            ax2.legend(fontsize=8)
            ax2.spines[["top", "right"]].set_visible(False)
            ax2.grid(alpha=0.3)
            st.pyplot(fig2)
            plt.close(fig2)
        else:
            st.warning("Break-even is beyond 36 months or not achievable. Chart suppressed.")

    with col_roi:
        st.markdown("**Break-Even Summary**")
        be_df = pd.DataFrame(
            {
                "Metric": ["Break-Even Timeline", "12-Month ROI", "Implementation Cost", "Annual Revenue Gain"],
                "Value": [
                    breakeven["payback_period_label"],
                    f"{breakeven['roi_12_months']:.0%}" if breakeven["roi_12_months"] != -1 else "N/A",
                    f"₹{implementation_cost:,.0f}",
                    f"₹{impact['incremental_revenue_annual']:,.0f}",
                ],
            }
        )
        st.dataframe(be_df, use_container_width=True, hide_index=True)

    # Go/No-Go verdict
    st.markdown("### Go / No-Go Recommendation")
    decision = rec["decision"]
    confidence = rec["confidence"]

    if decision == "GO":
        verdict_color = "success"
        icon = "✅"
    elif decision == "NO-GO":
        verdict_color = "error"
        icon = "❌"
    else:
        verdict_color = "warning"
        icon = "⚠️"

    verdict_fn = getattr(st, verdict_color)
    verdict_fn(
        f"{icon} **{decision}** — Confidence: **{confidence}**\n\n"
        + "\n\n".join(f"- {r}" for r in rec["reasons"])
    )

    with st.expander("Decision framework explained"):
        st.markdown(
            """
The Go/No-Go decision requires **three gates** to all pass:

| Gate | Criterion | Why it matters |
|---|---|---|
| **Statistical significance** | p-value < α | Rules out noise — confirms the effect is real |
| **Practical significance** | Relative lift ≥ 5% | Filters out real-but-trivial effects not worth shipping |
| **Business viability** | Break-even ≤ 6 months | Ensures positive ROI within a planning horizon |

A result can be statistically significant but still a **NO-GO** if the lift is
too small to justify the cost, or the payback window exceeds planning horizons.
This framework separates "the test worked" from "we should ship".
"""
        )

else:
    st.info("👆 Configure parameters in the sidebar, then click **▶ Run Simulation** to see results.")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.divider()
st.caption(
    "Built as a portfolio project demonstrating end-to-end A/B test design, "
    "statistical analysis, and business decision framing. "
    "All data is synthetic. Revenue figures use stated assumptions only."
)
