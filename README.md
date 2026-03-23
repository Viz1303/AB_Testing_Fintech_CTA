# A/B Test Decision Engine — Fintech Loan CTA


>
> *See the deployment instructions below to get this live in under 5 minutes (free, no server needed).*

---

## What is this project?

This is an end-to-end **A/B testing simulator and decision tool** built for a fintech scenario —
testing whether a redesigned loan offer button increases applications.

It demonstrates the full experiment lifecycle that data-driven product teams run every day:

| Step | What it does |
|---|---|
| **Plan** | Calculate how many users you need before starting the test |
| **Simulate** | Generate realistic synthetic test data with one click |
| **Analyse** | Run statistical tests and check if the result is real or noise |
| **Decide** | Translate the result into a revenue impact and a Go/No-Go recommendation |

**Everything is interactive** — adjust any parameter in the sidebar and the entire analysis updates in real time.

---

## Live Demo

> **Try the live app →** 🔗 [LIVE APP](https://abtestingfintech.streamlit.app)

To deploy your own copy:

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **"New app"** → select this repo → set main file to `app.py` → click **Deploy**
4. Streamlit gives you a public URL — paste it above

---

## The Scenario

**Company:** A fintech lending app offering personal loans to salaried professionals.

**The question:** Will changing the CTA button from *"Apply Now"* to *"Get ₹2.5L in 24 hours — Check Eligibility"* increase the number of users who start a loan application?

**Why this matters:** Even a small improvement in this conversion rate — say, from 4.2% to 5.0% — translates to hundreds of additional loan applications per month and significant fee revenue at scale.

**How the revenue works:** Each completed application generates a processing fee (~₹1,500 on a ₹2.5L loan). The tool calculates whether the lift from the new CTA justifies the cost of building it.

---

## How to Run Locally

```bash
# 1. Clone the repo and navigate into it
git clone <your-repo-url>
cd AB_Testing_Fintech_CTA

# 2. Install dependencies (Python 3.9+)
pip install -r requirements.txt

# 3. Launch the app
streamlit run app.py
```

Opens at `http://localhost:8501`. All inputs are in the left sidebar.

---

## What You Can Do in the App

**Left sidebar — tune any parameter:**
- Baseline conversion rate, minimum detectable effect, significance level, statistical power
- Monthly user volume, revenue per conversion, implementation cost
- The "true lift" baked into the simulation (to test what happens under different scenarios)

**Section 1 — Sample Size Planning**
Shows how many users you need before starting the test, and how that changes with different effect size targets. Answers: *"How long does this test need to run?"*

**Section 2 — Simulate & Analyse**
One button generates synthetic test data and runs two statistical tests. Shows conversion rates with confidence intervals, p-value, and relative lift. Answers: *"Is this result real or just noise?"*

**Section 3 — Business Impact & Go/No-Go**
Translates the statistical result into monthly/annual revenue projections, a break-even chart, and a clear GO / NO-GO / NEEDS MORE DATA recommendation with written reasoning. Answers: *"Should we ship this?"*

---

## The Go/No-Go Decision Framework

A result being "statistically significant" doesn't automatically mean you should ship it.
This tool applies **three gates** before recommending GO:

| Gate | What it checks | Why it matters |
|---|---|---|
| Statistical significance | Is the result unlikely to be random? (p < 0.05) | Rules out noise |
| Practical significance | Is the lift large enough to matter? (≥5% relative) | Filters out real-but-tiny effects not worth the cost |
| Business viability | Does the revenue pay back the build cost within 6 months? | Ensures positive ROI |

**All three must pass for a GO.** This mirrors how rigorous product teams actually make shipping decisions — not just "the test worked" but "the test worked *and* it's worth it."

---

## Skills Demonstrated

| Skill Area | Details |
|---|---|
| Experiment design | Power analysis, sample size calculation, MDE selection, significance levels |
| Statistical analysis | Two-proportion z-test, chi-square test, Wilson confidence intervals, relative lift |
| Business thinking | Revenue modelling, break-even analysis, assumption documentation, ROI framing |
| Python | `scipy`, `statsmodels`, `pandas`, `numpy`, `matplotlib`, modular package structure |
| Product tooling | Streamlit interactive app, real-time parameter sensitivity |
| Communication | Plain-English explanations of statistical concepts for non-technical stakeholders |

---

## Project Structure

```
AB_Testing_Fintech_CTA/
├── app.py                    # Streamlit app — run this to launch
├── modules/
│   ├── sample_size.py        # Sample size calculator + sensitivity table
│   ├── simulator.py          # Synthetic data generation engine
│   ├── stats_engine.py       # Statistical tests, confidence intervals, lift metrics
│   └── business_impact.py   # Revenue projections, break-even, Go/No-Go logic
├── requirements.txt          # Python dependencies
└── README.md
```

The `modules/` package keeps statistical logic, simulation, and business logic fully
separated from the UI — each module can be read, tested, or reused independently.

---

## A Note on the Data

All data is **100% synthetic**. No real user data was used at any point.
Conversion outcomes are generated using Bernoulli draws
(the same statistical model as real binary outcomes like "clicked" / "didn't click").
The random seed in the sidebar makes results reproducible — share a seed with someone
and they'll see the exact same simulated experiment.

---

## Statistical Methodology (for technical reviewers)

- **Sample size:** Cohen's h effect size solved via `statsmodels NormalIndPower`
- **Z-test vs Chi-square:** Both included intentionally. For a 2×2 table, χ² = z² — they are mathematically equivalent. The z-test is used for the directional decision; chi-square is shown to demonstrate awareness of their relationship.
- **Wilson CI over normal approximation:** For conversion rates in the 2–6% range, the normal approximation can produce negative lower bounds. Wilson intervals have better coverage properties at low rates and are the correct choice here.

---

*Portfolio project — all revenue figures use stated assumptions only.*
