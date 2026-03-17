"""
simulator.py
Generates synthetic A/B test data using Bernoulli draws.
Each row represents one user; groups are assigned with equal probability.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def simulate_ab_test(
    n_control: int,
    n_treatment: int,
    control_conversion: float,
    treatment_conversion: float,
    revenue_per_conversion: float = 1_500.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic A/B test dataset.

    Parameters
    ----------
    n_control : int
        Number of users in the control group
    n_treatment : int
        Number of users in the treatment (new CTA) group
    control_conversion : float
        True conversion probability for control
    treatment_conversion : float
        True conversion probability for treatment
    revenue_per_conversion : float
        INR revenue generated per conversion (e.g. loan processing fee)
    seed : int
        Random seed for reproducibility

    Returns
    -------
    pd.DataFrame with columns:
        user_id, group, converted, revenue, timestamp
    """
    rng = np.random.default_rng(seed)
    n_total = n_control + n_treatment

    # Generate Bernoulli draws
    control_conversions = rng.binomial(1, control_conversion, n_control)
    treatment_conversions = rng.binomial(1, treatment_conversion, n_treatment)

    # Simulate timestamps spread over the test window (last 30 days)
    base_date = datetime(2025, 11, 1)
    control_timestamps = [
        base_date + timedelta(seconds=int(s))
        for s in rng.uniform(0, 30 * 86400, n_control)
    ]
    treatment_timestamps = [
        base_date + timedelta(seconds=int(s))
        for s in rng.uniform(0, 30 * 86400, n_treatment)
    ]

    control_df = pd.DataFrame(
        {
            "user_id": range(1, n_control + 1),
            "group": "control",
            "converted": control_conversions,
            "revenue": control_conversions * revenue_per_conversion,
            "timestamp": control_timestamps,
        }
    )

    treatment_df = pd.DataFrame(
        {
            "user_id": range(n_control + 1, n_total + 1),
            "group": "treatment",
            "converted": treatment_conversions,
            "revenue": treatment_conversions * revenue_per_conversion,
            "timestamp": treatment_timestamps,
        }
    )

    df = pd.concat([control_df, treatment_df], ignore_index=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def get_summary_stats(df: pd.DataFrame) -> dict:
    """
    Aggregate the raw simulation DataFrame into per-group summary statistics.

    Returns
    -------
    dict with keys 'control' and 'treatment', each containing:
        n, conversions, rate, revenue
    """
    summary = {}
    for group in ["control", "treatment"]:
        subset = df[df["group"] == group]
        n = len(subset)
        conversions = subset["converted"].sum()
        summary[group] = {
            "n": n,
            "conversions": int(conversions),
            "rate": conversions / n if n > 0 else 0.0,
            "revenue": subset["revenue"].sum(),
        }
    return summary
