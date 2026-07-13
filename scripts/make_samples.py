#!/usr/bin/env python3
"""Generate 3 curated demo CSVs by sampling real scored accounts.

Sampling from the actual scored portfolio guarantees the intended RAG mix for
a reliable live demo. Outputs to frontend/public/samples/:
  - low_risk_portfolio.csv     (healthy MSMEs, all GREEN)
  - mixed_portfolio.csv        (realistic spread: GREEN + AMBER + RED)
  - high_risk_watchlist.csv    (stressed MSMEs, all RED)
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ML = ROOT / "ml"
sys.path.insert(0, str(ML))

from features import engineer_features  # noqa: E402
from segments import get_rag_bucket  # noqa: E402

INPUT_COLUMNS = [
    "account_id", "loan_type", "borrower_profile", "enterprise_size", "sector",
    "region", "loan_amount", "tenure_months", "interest_rate", "vintage_months",
    "collateral_coverage", "bureau_score", "turnover", "gst_sales", "foir",
    "dpd_max_12m", "emi_bounces_12m", "avg_balance_trend", "cc_utilization",
    "gst_filing_delay_days", "txn_volume_trend", "cheque_returns_12m",
    "min_balance_breaches_12m", "rm_notes",
]


def score_portfolio(model, feature_cols) -> pd.DataFrame:
    raw = pd.read_parquet(ML / "data" / "msme_panel.parquet")
    f = engineer_features(raw.copy(), fit=False)
    cols = [c for c in feature_cols if c in f.columns]
    X = np.zeros((len(f), len(feature_cols)), dtype=np.float32)
    idx = {c: i for i, c in enumerate(feature_cols)}
    for c in cols:
        X[:, idx[c]] = f[c].fillna(0).values
    raw["predicted_pd"] = model.predict_proba(X)[:, 1]
    raw["rag"] = [get_rag_bucket(p, lt) for p, lt in zip(raw["predicted_pd"], raw["loan_type"])]
    return raw


def relabel(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    df = df.copy().reset_index(drop=True)
    df["account_id"] = [f"{prefix}-{i + 1:02d}" for i in range(len(df))]
    return df[INPUT_COLUMNS]


def main():
    out = ROOT / "frontend" / "public" / "samples"
    out.mkdir(parents=True, exist_ok=True)
    model = joblib.load(ML / "models" / "model.joblib")
    feature_cols = joblib.load(ML / "models" / "feature_columns.joblib")

    scored = score_portfolio(model, feature_cols)
    rng = np.random.default_rng(7)

    green = scored[scored["rag"] == "green"].sort_values("predicted_pd")
    amber = scored[scored["rag"] == "amber"].sort_values("predicted_pd")
    red = scored[scored["rag"] == "red"].sort_values("predicted_pd", ascending=False)

    # Low risk: 6 healthiest green accounts
    low = relabel(green.head(30).sample(6, random_state=1), "MSME-DEMO-LOW")

    # Mixed: 4 green + 3 amber + 2 red
    mixed = pd.concat([
        green.sample(4, random_state=2),
        amber.sample(min(3, len(amber)), random_state=3),
        red.head(15).sample(2, random_state=4),
    ])
    mixed = relabel(mixed, "MSME-DEMO-MIX")

    # High risk: 6 highest-PD red accounts
    high = relabel(red.head(20).sample(6, random_state=5), "MSME-DEMO-HIGH")

    datasets = {
        "low_risk_portfolio.csv": low,
        "mixed_portfolio.csv": mixed,
        "high_risk_watchlist.csv": high,
    }

    for fname, df in datasets.items():
        df.to_csv(out / fname, index=False)
        f = engineer_features(df.copy(), fit=False)
        cols = [c for c in feature_cols if c in f.columns]
        X = np.zeros((len(f), len(feature_cols)), dtype=np.float32)
        idx = {c: i for i, c in enumerate(feature_cols)}
        for c in cols:
            X[:, idx[c]] = f[c].fillna(0).values
        p = model.predict_proba(X)[:, 1]
        rags = [get_rag_bucket(a, b) for a, b in zip(p, df["loan_type"])]
        dist = pd.Series(rags).value_counts().to_dict()
        print(f"{fname:26s} n={len(df):2d} PD[min/mean/max]="
              f"{p.min():.2f}/{p.mean():.2f}/{p.max():.2f}  RAG={dist}")

    print(f"\nSaved 3 sample datasets to {out}")


if __name__ == "__main__":
    main()
