"""
stats_engine.py
Statistical analysis for the A/B test.

Includes:
  - Two-proportion z-test (proportions_ztest)
  - Chi-square test on a 2x2 contingency table
  - Wilson confidence intervals (preferred over normal approx for small rates)
  - Relative and absolute lift calculations

Note: chi2 = z^2 for a 2x2 table with a two-sided alternative.
Both are included here intentionally to demonstrate awareness of their equivalence.
"""

import math
import numpy as np
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportions_ztest, proportion_confint


def run_z_test(
    n_control: int,
    conv_control: int,
    n_treatment: int,
    conv_treatment: int,
    alpha: float = 0.05,
) -> dict:
    """
    Two-proportion z-test (two-sided).

    Returns
    -------
    dict: z_stat, p_value, significant, control_rate, treatment_rate
    """
    counts = np.array([conv_treatment, conv_control])
    nobs = np.array([n_treatment, n_control])
    z_stat, p_value = proportions_ztest(counts, nobs, alternative="two-sided")

    return {
        "z_stat": round(float(z_stat), 4),
        "p_value": round(float(p_value), 6),
        "significant": bool(p_value < alpha),
        "control_rate": conv_control / n_control,
        "treatment_rate": conv_treatment / n_treatment,
    }


def run_chi_square_test(
    n_control: int,
    conv_control: int,
    n_treatment: int,
    conv_treatment: int,
    alpha: float = 0.05,
) -> dict:
    """
    Chi-square test of independence on a 2x2 contingency table.
    Equivalent to the two-sided z-test: chi2_stat ≈ z_stat^2.

    Returns
    -------
    dict: chi2_stat, p_value, significant, cramers_v
    """
    # Contingency table: rows = converted/not, cols = treatment/control
    table = np.array(
        [
            [conv_treatment, conv_control],
            [n_treatment - conv_treatment, n_control - conv_control],
        ]
    )
    chi2_stat, p_value, dof, expected = chi2_contingency(table, correction=False)

    # Cramer's V as effect size (for 2x2: sqrt(chi2 / n))
    n_total = n_control + n_treatment
    cramers_v = math.sqrt(chi2_stat / n_total)

    return {
        "chi2_stat": round(float(chi2_stat), 4),
        "p_value": round(float(p_value), 6),
        "significant": bool(p_value < alpha),
        "cramers_v": round(cramers_v, 4),
    }


def confidence_interval(
    n: int,
    conversions: int,
    confidence: float = 0.95,
) -> tuple:
    """
    Wilson confidence interval for a proportion.

    Wilson is preferred over the normal approximation when conversion rates
    are low (< 10%) or sample sizes are moderate, as it avoids negative bounds
    and has better coverage properties.

    Returns
    -------
    (lower, upper) as floats
    """
    lower, upper = proportion_confint(
        count=conversions, nobs=n, alpha=1 - confidence, method="wilson"
    )
    return (round(float(lower), 6), round(float(upper), 6))


def relative_lift(control_rate: float, treatment_rate: float) -> float:
    """Relative lift: (treatment - control) / control."""
    if control_rate == 0:
        return 0.0
    return (treatment_rate - control_rate) / control_rate


def absolute_lift(control_rate: float, treatment_rate: float) -> float:
    """Absolute lift in percentage points."""
    return treatment_rate - control_rate


def full_analysis(summary: dict, alpha: float = 0.05) -> dict:
    """
    Run a complete statistical analysis from the summary dict produced
    by simulator.get_summary_stats().

    Returns a consolidated results dict consumed by the Streamlit app.
    """
    ctrl = summary["control"]
    trt = summary["treatment"]

    z_results = run_z_test(
        n_control=ctrl["n"],
        conv_control=ctrl["conversions"],
        n_treatment=trt["n"],
        conv_treatment=trt["conversions"],
        alpha=alpha,
    )

    chi2_results = run_chi_square_test(
        n_control=ctrl["n"],
        conv_control=ctrl["conversions"],
        n_treatment=trt["n"],
        conv_treatment=trt["conversions"],
        alpha=alpha,
    )

    ctrl_ci = confidence_interval(ctrl["n"], ctrl["conversions"])
    trt_ci = confidence_interval(trt["n"], trt["conversions"])

    rel_lift = relative_lift(ctrl["rate"], trt["rate"])
    abs_lift = absolute_lift(ctrl["rate"], trt["rate"])

    return {
        "z_test": z_results,
        "chi2_test": chi2_results,
        "control_ci": ctrl_ci,
        "treatment_ci": trt_ci,
        "relative_lift": round(rel_lift, 4),
        "absolute_lift": round(abs_lift, 6),
        "significant": z_results["significant"],
        "p_value": z_results["p_value"],
        "alpha": alpha,
    }
