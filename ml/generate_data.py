"""Synthetic MSME panel generator for default-within-12-months prediction."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from segments import BORROWER_PROFILES, ENTERPRISE_SIZES, LOAN_TYPES

SEED = 42
SECTORS = [
    "manufacturing",
    "trading",
    "services",
    "logistics",
    "agri_processing",
    "textiles",
]
REGIONS = ["north", "south", "west", "east", "central"]

RM_NOTE_TEMPLATES_SAFE = [
    "Customer maintains regular EMI payments. Business turnover stable.",
    "GST filings on time. Adequate working capital maintained.",
    "Positive interaction during branch visit. No adverse remarks.",
    "Seasonal business showing expected recovery post-festival period.",
]

RM_NOTE_TEMPLATES_RISK = [
    "Customer reported cash flow stress due to delayed receivables.",
    "GST filing delayed by {delay} days. EMI bounce observed last month.",
    "Sector headwinds noted. Customer seeking additional working capital.",
    "Cheque return observed. Balance trending below minimum threshold.",
    "Delayed supplier payments mentioned during RM call.",
]

# Risk loadings applied to latent default risk. These make borrower profile,
# enterprise size and sector CARRY REAL (small) signal - matching observed
# MSME NPA patterns - instead of being decorative columns.
PROFILE_RISK = {"ntc": 0.14, "ntb": 0.07, "etb": 0.0}  # thin-file borrowers riskier
SIZE_RISK = {"micro": 0.06, "small": 0.02, "medium": 0.0}  # micro most fragile
SECTOR_RISK = {  # relative sector stress (textiles/agri historically hotter)
    "textiles": 0.05, "agri_processing": 0.04, "logistics": 0.03,
    "trading": 0.02, "services": 0.01, "manufacturing": 0.0,
}
# Enterprise-size scale bands (Udyam / MSMED Act turnover thresholds, INR):
# micro <= Rs 5 Cr, small <= Rs 50 Cr, medium <= Rs 250 Cr.
SIZE_TURNOVER = {
    "micro": (1.5e7, 2.5e6, 5e7),
    "small": (1.5e8, 5e7, 5e8),
    "medium": (8e8, 5e8, 2.5e9),
}
# Base collateral coverage by product: LAP property-secured (high), CC current-
# asset / drawing-power based (lower), equipment tracks asset value, term mixed.
LOANTYPE_COLLATERAL = {
    "lap": 1.65, "equipment_finance": 1.05, "term_loan": 0.95, "cash_credit": 0.80,
}


def _latent_risk(
    rng: np.random.Generator,
    borrower_profile: np.ndarray,
    enterprise_size: np.ndarray,
    sector: np.ndarray,
) -> np.ndarray:
    """Latent default risk (0-1) built from the ACTUAL assigned segment
    attributes, so profile/size/sector genuinely drive risk."""
    n = len(borrower_profile)
    base = rng.beta(2, 8, n)
    prof = np.array([PROFILE_RISK[p] for p in borrower_profile])
    size = np.array([SIZE_RISK[s] for s in enterprise_size])
    sect = np.array([SECTOR_RISK[s] for s in sector])
    noise = rng.normal(0, 0.05, n)
    return np.clip(base + prof + size + sect + noise, 0.01, 0.99)


def _generate_accounts(rng: np.random.Generator, n: int) -> pd.DataFrame:
    # Segment attributes drawn FIRST, then latent risk computed from them -
    # profile/size/sector are real risk drivers, not decorative labels.
    loan_type = rng.choice(LOAN_TYPES, n)
    borrower_profile = rng.choice(BORROWER_PROFILES, n, p=[0.2, 0.3, 0.5])
    enterprise_size = rng.choice(ENTERPRISE_SIZES, n, p=[0.35, 0.45, 0.20])
    sector = rng.choice(SECTORS, n)
    region = rng.choice(REGIONS, n)

    latent = _latent_risk(rng, borrower_profile, enterprise_size, sector)

    # -- Observed features are NOISY proxies of latent risk, not deterministic
    # projections. Heavy idiosyncratic noise means the model can partially, but
    # never perfectly, reconstruct the underlying risk. Target bank-grade
    # AUC ~0.79 / KS ~0.45 rather than the implausible >0.90 that signals leakage.

    # Turnover scaled to enterprise size (Udyam-consistent); loan a modest
    # fraction of turnover, capped at Rs 15 Cr so the book reads as MSME.
    centers = np.array([SIZE_TURNOVER[s][0] for s in enterprise_size])
    lows = np.array([SIZE_TURNOVER[s][1] for s in enterprise_size])
    highs = np.array([SIZE_TURNOVER[s][2] for s in enterprise_size])
    turnover = np.clip(rng.lognormal(np.log(centers), 0.45), lows, highs)
    loan_amount = (turnover * rng.uniform(0.06, 0.22, n)).clip(300_000, 1.5e8)
    gst_sales = turnover * rng.uniform(0.80, 1.00, n)  # cannot exceed turnover

    tenure_months = rng.integers(12, 84, n)
    interest_rate = (10.0 + latent * 3.0 + rng.normal(0, 1.2, n)).clip(9.5, 16.5)
    vintage_months = rng.integers(6, 120, n)
    base_cov = np.array([LOANTYPE_COLLATERAL[lt] for lt in loan_type])
    collateral_coverage = (base_cov - latent * 0.4 + rng.normal(0, 0.25, n)).clip(0.0, 2.5)
    # CIBIL-style commercial bureau scale (300-900).
    bureau_score = (720 - latent * 170 + rng.normal(0, 28, n)).clip(300, 900)
    foir = (0.30 + latent * 0.26 + rng.normal(0, 0.06, n)).clip(0.1, 0.85)

    # Behavioral features: correlated with latent risk but with real dispersion.
    # DPD capped at 89: the scored population is the PERFORMING book
    # (Standard / SMA-0/1/2 under RBI IRAC norms); 90+ DPD accounts are
    # already NPA and belong in collections, not an early-warning model.
    dpd_max_12m = (latent * 65 + rng.exponential(6, n)).clip(0, 89).astype(int)
    emi_bounces_12m = rng.poisson(np.clip(latent * 4.0 + 0.3, 0, None)).clip(0, 12).astype(int)
    avg_balance_trend = (0.04 - latent * 0.11 + rng.normal(0, 0.045, n)).clip(-0.3, 0.2)
    cc_utilization = (0.45 + latent * 0.35 + rng.normal(0, 0.09, n)).clip(0.05, 0.99)
    gst_filing_delay_days = (latent * 34 + rng.exponential(4, n)).clip(0, 90).astype(int)
    txn_volume_trend = (0.02 - latent * 0.08 + rng.normal(0, 0.07, n)).clip(-0.35, 0.25)
    cheque_returns_12m = rng.poisson(np.clip(latent * 2.0 + 0.15, 0, None)).clip(0, 10).astype(int)
    min_balance_breaches_12m = rng.poisson(np.clip(latent * 4.0 + 0.4, 0, None)).clip(0, 15).astype(int)

    # Public-domain / alternate data (the problem statement's third mandated
    # input class, alongside borrower behavior and bank-internal data):
    # electricity consumption trend (state discom data - production proxy),
    # EPFO payroll headcount trend (employment stress), Udyam registration
    # status (formalization signal). Noisy proxies like all other features.
    electricity_consumption_trend = (0.03 - latent * 0.10 + rng.normal(0, 0.06, n)).clip(-0.4, 0.3)
    epfo_headcount_trend = (0.02 - latent * 0.08 + rng.normal(0, 0.05, n)).clip(-0.35, 0.25)
    udyam_registered = (rng.random(n) < (0.92 - latent * 0.20)).astype(int)

    # Label: default within next 12 months. Driven by latent risk PLUS an
    # UNOBSERVED shock (fraud, promoter issues, sudden order loss) that no
    # feature captures - this heterogeneity caps achievable discrimination at a
    # realistic level and mimics the irreducible uncertainty of real defaults.
    unobserved_shock = rng.normal(0, 1.0, n)
    logit = -6.05 + 9.0 * latent + 0.90 * unobserved_shock + 0.006 * dpd_max_12m
    default_prob = 1.0 / (1.0 + np.exp(-logit))
    default_12m = (rng.random(n) < default_prob).astype(int)

    # Month within the 12-month horizon when default crystallises (NPA slippage),
    # used to quantify early-warning lead time. Higher-risk accounts slip modestly
    # earlier; non-defaulters = 0. Observed only in hindsight; never a feature.
    month_raw = rng.normal(7.5 - 2.0 * latent, 2.6, n)
    month_to_default = np.where(
        default_12m == 1, np.clip(np.round(month_raw), 1, 12), 0
    ).astype(int)

    # Unstructured text: RM notes are a NOISY textual signal.
    note_is_risk = (latent + rng.normal(0, 0.18, n)) > 0.5
    rm_notes = []
    for i in range(n):
        if note_is_risk[i]:
            template = rng.choice(RM_NOTE_TEMPLATES_RISK)
            rm_notes.append(
                template.format(delay=int(gst_filing_delay_days[i]))
                if "{delay}" in template
                else template
            )
        else:
            rm_notes.append(rng.choice(RM_NOTE_TEMPLATES_SAFE))

    account_ids = [f"MSME-{100000 + i:06d}" for i in range(n)]

    return pd.DataFrame(
        {
            "account_id": account_ids,
            "loan_type": loan_type,
            "borrower_profile": borrower_profile,
            "enterprise_size": enterprise_size,
            "sector": sector,
            "region": region,
            "loan_amount": loan_amount.round(2),
            "tenure_months": tenure_months,
            "interest_rate": interest_rate.round(2),
            "vintage_months": vintage_months,
            "collateral_coverage": collateral_coverage.round(2),
            "bureau_score": bureau_score.round(0),
            "turnover": turnover.round(2),
            "gst_sales": gst_sales.round(2),
            "foir": foir.round(3),
            "dpd_max_12m": dpd_max_12m,
            "emi_bounces_12m": emi_bounces_12m,
            "avg_balance_trend": avg_balance_trend.round(4),
            "cc_utilization": cc_utilization.round(4),
            "gst_filing_delay_days": gst_filing_delay_days,
            "txn_volume_trend": txn_volume_trend.round(4),
            "cheque_returns_12m": cheque_returns_12m,
            "min_balance_breaches_12m": min_balance_breaches_12m,
            "electricity_consumption_trend": electricity_consumption_trend.round(4),
            "epfo_headcount_trend": epfo_headcount_trend.round(4),
            "udyam_registered": udyam_registered,
            "rm_notes": rm_notes,
            "latent_risk": latent.round(4),
            "default_12m": default_12m,
            "month_to_default": month_to_default,
        }
    )


def generate_dataset(n_accounts: int = 20000, output_dir: str | Path = "data") -> Path:
    """Generate and persist synthetic MSME panel."""
    rng = np.random.default_rng(SEED)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df = _generate_accounts(rng, n_accounts)
    parquet_path = output_path / "msme_panel.parquet"
    csv_path = output_path / "msme_panel.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    print(f"Generated {len(df)} accounts | default rate: {df['default_12m'].mean():.2%}")
    print(f"Saved to {parquet_path}")
    return parquet_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic MSME panel")
    parser.add_argument("--n", type=int, default=20000, help="Number of accounts")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    generate_dataset(args.n, args.output)
