"""
sample_size.py
Calculates required sample size per group for a two-proportion z-test.
Uses Cohen's h effect size and the normal approximation to the binomial.
"""

import pandas as pd
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.power import NormalIndPower


def calculate_sample_size(
    baseline_conversion: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_tailed: bool = True,
    daily_traffic: int = 1_667,  # users/day exposed to the test
) -> dict:
    """
    Calculate required sample size per group.

    Parameters
    ----------
    baseline_conversion : float
        Current conversion rate, e.g. 0.042 for 4.2%
    mde : float
        Minimum detectable effect as a *relative* lift, e.g. 0.20 = 20% relative lift
    alpha : float
        Significance level (Type I error rate)
    power : float
        Statistical power (1 - Type II error rate)
    two_tailed : bool
        Whether to use a two-tailed test
    daily_traffic : int
        Daily users split equally across both groups

    Returns
    -------
    dict with keys: n_per_group, total_n, control_rate, treatment_rate,
                    effect_size, estimated_days
    """
    treatment_rate = baseline_conversion * (1 + mde)
    effect_size = proportion_effectsize(treatment_rate, baseline_conversion)

    analysis = NormalIndPower()
    ratio = 1.0  # equal group sizes

    n_per_group = analysis.solve_power(
        effect_size=abs(effect_size),
        alpha=alpha / (2 if two_tailed else 1),  # one-tailed alpha if needed
        power=power,
        ratio=ratio,
        alternative="two-sided" if two_tailed else "larger",
    )
    n_per_group = int(n_per_group) + 1  # ceiling
    total_n = n_per_group * 2
    daily_per_group = daily_traffic / 2
    estimated_days = total_n / daily_traffic

    return {
        "n_per_group": n_per_group,
        "total_n": total_n,
        "control_rate": baseline_conversion,
        "treatment_rate": round(treatment_rate, 6),
        "effect_size": round(abs(effect_size), 4),
        "estimated_days": round(estimated_days, 1),
        "daily_traffic": daily_traffic,
    }


def sample_size_sensitivity_table(
    baseline_conversion: float,
    mde_range: list,
    alpha: float = 0.05,
    power: float = 0.80,
    daily_traffic: int = 1_667,
) -> pd.DataFrame:
    """
    Generate a sensitivity table showing how sample size changes with MDE.

    Returns a DataFrame with columns:
    MDE (Relative), Treatment Rate, N per Group, Total N, Est. Duration (Days)
    """
    rows = []
    for mde in mde_range:
        result = calculate_sample_size(
            baseline_conversion=baseline_conversion,
            mde=mde,
            alpha=alpha,
            power=power,
            daily_traffic=daily_traffic,
        )
        rows.append(
            {
                "MDE (Relative)": f"{mde:.0%}",
                "Treatment Rate": f"{result['treatment_rate']:.2%}",
                "N per Group": f"{result['n_per_group']:,}",
                "Total N": f"{result['total_n']:,}",
                "Est. Duration (Days)": result["estimated_days"],
            }
        )
    return pd.DataFrame(rows)
