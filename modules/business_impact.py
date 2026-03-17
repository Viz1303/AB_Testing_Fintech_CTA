"""
business_impact.py
Translates statistical test results into business decisions.

Assumptions (explicitly stated for PM review):
  - Revenue per conversion = loan processing fee (not the loan principal)
  - Monthly user volume is the total number of users who see the CTA
  - Implementation cost = one-time engineering + design effort
  - Conservative estimate = 80% of point estimate (accounts for novelty effect decay)
  - Optimistic estimate = 120% of point estimate
"""


def revenue_impact(
    n_monthly_users: int,
    control_rate: float,
    treatment_rate: float,
    revenue_per_conversion: float,
) -> dict:
    """
    Estimate the incremental monthly and annual revenue from rolling out the treatment.

    Parameters
    ----------
    n_monthly_users : int
        Total users exposed to the CTA per month post-launch
    control_rate : float
        Baseline conversion rate (observed in test)
    treatment_rate : float
        Treatment conversion rate (observed in test)
    revenue_per_conversion : float
        Revenue generated per conversion in INR

    Returns
    -------
    dict: incremental_conversions_monthly, incremental_revenue_monthly,
          incremental_revenue_annual, conservative_revenue, optimistic_revenue
    """
    incremental_rate = treatment_rate - control_rate
    incremental_conversions_monthly = n_monthly_users * incremental_rate
    incremental_revenue_monthly = incremental_conversions_monthly * revenue_per_conversion
    incremental_revenue_annual = incremental_revenue_monthly * 12

    return {
        "incremental_conversions_monthly": round(incremental_conversions_monthly, 1),
        "incremental_revenue_monthly": round(incremental_revenue_monthly, 2),
        "incremental_revenue_annual": round(incremental_revenue_annual, 2),
        "conservative_revenue": round(incremental_revenue_monthly * 0.80, 2),
        "optimistic_revenue": round(incremental_revenue_monthly * 1.20, 2),
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
    }


def break_even_analysis(
    implementation_cost: float,
    incremental_revenue_monthly: float,
) -> dict:
    """
    Calculate break-even timeline and 12-month ROI.

    Parameters
    ----------
    implementation_cost : float
        One-time cost to implement and ship the new CTA (INR)
    incremental_revenue_monthly : float
        Expected incremental revenue per month post-launch (INR)

    Returns
    -------
    dict: break_even_months, roi_12_months, payback_period_label
    """
    if incremental_revenue_monthly <= 0:
        return {
            "break_even_months": float("inf"),
            "roi_12_months": -1.0,
            "payback_period_label": "Never (no positive lift)",
        }

    break_even_months = implementation_cost / incremental_revenue_monthly
    annual_gain = incremental_revenue_monthly * 12
    roi_12_months = (annual_gain - implementation_cost) / implementation_cost

    if break_even_months < 1:
        label = "< 1 month"
    elif break_even_months <= 24:
        label = f"{break_even_months:.1f} months"
    else:
        label = f"{break_even_months / 12:.1f} years"

    return {
        "break_even_months": round(break_even_months, 2),
        "roi_12_months": round(roi_12_months, 4),
        "payback_period_label": label,
    }


def go_no_go_recommendation(
    p_value: float,
    rel_lift: float,
    break_even_months: float,
    alpha: float = 0.05,
    min_lift_threshold: float = 0.05,
    max_payback_months: float = 6.0,
) -> dict:
    """
    Rule-based Go/No-Go decision engine.

    Three gates, evaluated in order:
    1. Statistical significance  — p_value < alpha
    2. Practical significance    — relative lift >= min_lift_threshold
    3. Business viability        — break-even <= max_payback_months

    All three must pass for a GO decision.

    Returns
    -------
    dict: decision ('GO' | 'NO-GO' | 'NEEDS MORE DATA'),
          reasons (list of strings), confidence ('High' | 'Medium' | 'Low')
    """
    reasons = []
    gates_passed = 0

    # Gate 1: Statistical significance
    if p_value < alpha:
        reasons.append(
            f"Statistically significant: p={p_value:.4f} < α={alpha} (low probability this is noise)"
        )
        gates_passed += 1
    else:
        reasons.append(
            f"NOT statistically significant: p={p_value:.4f} ≥ α={alpha} — result may be random chance"
        )

    # Gate 2: Practical significance
    if rel_lift >= min_lift_threshold:
        reasons.append(
            f"Meaningful lift: {rel_lift:.1%} relative improvement exceeds {min_lift_threshold:.0%} threshold"
        )
        gates_passed += 1
    elif rel_lift < 0:
        reasons.append(
            f"Negative lift: treatment performed {abs(rel_lift):.1%} WORSE than control — do not ship"
        )
    else:
        reasons.append(
            f"Lift too small: {rel_lift:.1%} is below the {min_lift_threshold:.0%} practical significance threshold"
        )

    # Gate 3: Business viability
    if break_even_months == float("inf"):
        reasons.append("No positive revenue impact — break-even is not achievable")
    elif break_even_months <= max_payback_months:
        reasons.append(
            f"Strong ROI: break-even in {break_even_months:.1f} months (threshold: {max_payback_months:.0f} months)"
        )
        gates_passed += 1
    else:
        reasons.append(
            f"Slow payback: break-even in {break_even_months:.1f} months exceeds {max_payback_months:.0f}-month threshold"
        )

    # Decision logic
    if rel_lift < 0 and p_value < alpha:
        decision = "NO-GO"
        confidence = "High"
    elif gates_passed == 3:
        decision = "GO"
        confidence = "High"
    elif gates_passed == 2:
        decision = "GO"
        confidence = "Medium"
    elif gates_passed == 1 and p_value >= alpha:
        decision = "NEEDS MORE DATA"
        confidence = "Low"
    else:
        decision = "NO-GO"
        confidence = "Medium"

    return {
        "decision": decision,
        "reasons": reasons,
        "confidence": confidence,
        "gates_passed": gates_passed,
    }
