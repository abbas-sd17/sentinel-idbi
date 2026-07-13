"""Feature engineering for MSME default prediction."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from segments import assign_segment

CATEGORICAL_COLS = [
    "loan_type",
    "borrower_profile",
    "enterprise_size",
    "sector",
    "region",
]

NUMERIC_COLS = [
    "loan_amount",
    "tenure_months",
    "interest_rate",
    "vintage_months",
    "collateral_coverage",
    "bureau_score",
    "turnover",
    "gst_sales",
    "foir",
    "dpd_max_12m",
    "emi_bounces_12m",
    "avg_balance_trend",
    "cc_utilization",
    "gst_filing_delay_days",
    "txn_volume_trend",
    "cheque_returns_12m",
    "min_balance_breaches_12m",
    # Public-domain / alternate data (problem statement's third mandated input
    # class): electricity consumption + EPFO payroll trends and Udyam status.
    "electricity_consumption_trend",
    "epfo_headcount_trend",
    "udyam_registered",
]

DISTRESS_KEYWORDS = [
    "stress",
    "delayed",
    "bounce",
    "adverse",
    "return",
    "below",
    "headwind",
    "seeking",
]

# Neutral defaults used to backfill any raw column a source (e.g. the Stage-2
# bank sandbox) does not supply. Missing behavioral/compliance signals default
# to 0 (no adverse event observed); categoricals default to the modal value.
# Makes scoring robust to schema drift: extra columns ignored, missing columns
# imputed, unseen category values become all-zero one-hots.
RAW_DEFAULTS: dict[str, object] = {
    "loan_type": "term_loan", "borrower_profile": "etb", "enterprise_size": "small",
    "sector": "manufacturing", "region": "west",
    "loan_amount": 1_000_000.0, "tenure_months": 36, "interest_rate": 12.0,
    "vintage_months": 24, "collateral_coverage": 1.0, "bureau_score": 700.0,
    "turnover": 5_000_000.0, "gst_sales": 4_500_000.0, "foir": 0.4,
    "dpd_max_12m": 0, "emi_bounces_12m": 0, "avg_balance_trend": 0.0,
    "cc_utilization": 0.5, "gst_filing_delay_days": 0, "txn_volume_trend": 0.0,
    "cheque_returns_12m": 0, "min_balance_breaches_12m": 0, "rm_notes": "",
    "electricity_consumption_trend": 0.0, "epfo_headcount_trend": 0.0,
    "udyam_registered": 1,
}


def missing_raw_columns(df: pd.DataFrame) -> list[str]:
    """Raw columns that will be backfilled with neutral defaults for at least
    one row. Callers scoring external files should surface these as warnings:
    neutral defaults mean 'no adverse event observed', so silently-imputed
    behavioral fields bias scores toward Green."""
    missing = []
    for col in RAW_DEFAULTS:
        if col not in df.columns or df[col].isna().any():
            missing.append(col)
    return missing

_tfidf_vectorizer: TfidfVectorizer | None = None


def get_vectorizer() -> TfidfVectorizer | None:
    """Return the fitted TF-IDF vectorizer (for persisting as an artifact)."""
    return _tfidf_vectorizer


def set_vectorizer(vectorizer: TfidfVectorizer | None) -> None:
    """Inject a pre-fitted TF-IDF vectorizer (loaded at inference time)."""
    global _tfidf_vectorizer
    _tfidf_vectorizer = vectorizer


def _nlp_distress_score(texts: pd.Series, fit: bool) -> np.ndarray:
    """Compute NLP distress score from RM notes using keyword + TF-IDF fusion.

    The TF-IDF density is normalized with constants FROZEN AT FIT TIME and
    persisted on the vectorizer artifact (density_min_/density_max_). This
    keeps the score deterministic per account: a single /predict call and a
    20k-row batch produce identical values (no batch-dependent min-max, no
    train/serve skew).
    """
    global _tfidf_vectorizer
    texts = texts.fillna("").astype(str)
    keyword_scores = texts.apply(
        lambda t: sum(1 for kw in DISTRESS_KEYWORDS if kw in t.lower()) / len(DISTRESS_KEYWORDS)
    ).values

    if fit:
        _tfidf_vectorizer = TfidfVectorizer(max_features=50, stop_words="english")
        tfidf_matrix = _tfidf_vectorizer.fit_transform(texts)
        tfidf_density = np.array(tfidf_matrix.mean(axis=1)).flatten()
        # Freeze normalization constants from the training corpus.
        _tfidf_vectorizer.density_min_ = float(tfidf_density.min())
        _tfidf_vectorizer.density_max_ = float(tfidf_density.max())
    else:
        if _tfidf_vectorizer is None:
            raise RuntimeError(
                "TF-IDF vectorizer artifact not loaded. Call set_vectorizer() "
                "with the fitted artifact before scoring (never re-fit on "
                "inference data)."
            )
        tfidf_matrix = _tfidf_vectorizer.transform(texts)
        tfidf_density = np.array(tfidf_matrix.mean(axis=1)).flatten()

    lo = getattr(_tfidf_vectorizer, "density_min_", 0.0)
    hi = getattr(_tfidf_vectorizer, "density_max_", 1.0)
    tfidf_norm = np.clip((tfidf_density - lo) / (hi - lo + 1e-9), 0.0, 1.0)
    return (0.6 * keyword_scores + 0.4 * tfidf_norm).clip(0, 1)


def engineer_features(df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
    """Build model-ready feature matrix from raw panel.

    fit=True fits the TF-IDF vectorizer on df (training only). fit=False
    requires a fitted vectorizer (loaded via set_vectorizer) and never
    re-fits — inference is strictly transform-only.
    """
    out = df.copy()
    # Backfill any missing raw columns with neutral defaults so the pipeline is
    # robust to schema drift (missing/renamed sandbox columns, partial feeds).
    # Callers scoring external data should report missing_raw_columns(df).
    for col, default in RAW_DEFAULTS.items():
        if col not in out.columns:
            out[col] = default
        else:
            out[col] = out[col].fillna(default)

    out["segment"] = out.apply(assign_segment, axis=1)
    out["nlp_distress_score"] = _nlp_distress_score(out["rm_notes"], fit=fit)

    # Derived ratios
    out["loan_to_turnover"] = (out["loan_amount"] / out["turnover"].clip(lower=1)).clip(0, 2)
    out["gst_turnover_ratio"] = (out["gst_sales"] / out["turnover"].clip(lower=1)).clip(0, 1.5)
    out["behavioral_stress_index"] = (
        out["dpd_max_12m"] / 90 * 0.3
        + out["emi_bounces_12m"] / 12 * 0.2
        + out["cc_utilization"] * 0.2
        + out["gst_filing_delay_days"] / 90 * 0.15
        + (1 - out["avg_balance_trend"].clip(-0.3, 0.2) / 0.5) * 0.15
    ).clip(0, 1)

    derived_numeric = ["loan_to_turnover", "gst_turnover_ratio", "behavioral_stress_index", "nlp_distress_score"]
    feature_cols = NUMERIC_COLS + derived_numeric

    # One-hot encode categoricals
    cat_dummies = pd.get_dummies(out[CATEGORICAL_COLS], prefix=CATEGORICAL_COLS, drop_first=False)
    numeric = out[feature_cols].astype(float)

    features = pd.concat([numeric, cat_dummies], axis=1)
    features["account_id"] = out["account_id"].values
    features["segment"] = out["segment"].values
    features["loan_type"] = out["loan_type"].values
    if "default_12m" in out.columns:
        features["default_12m"] = out["default_12m"].values
    if "latent_risk" in out.columns:
        features["latent_risk"] = out["latent_risk"].values
    if "month_to_default" in out.columns:
        features["month_to_default"] = out["month_to_default"].values

    return features


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """Return columns used for model training (exclude metadata)."""
    exclude = {"account_id", "segment", "loan_type", "default_12m", "latent_risk", "month_to_default"}
    return [c for c in df.columns if c not in exclude]


def features_from_dict(row: dict[str, Any], feature_columns: list[str]) -> np.ndarray:
    """Build feature vector from a single account dict for inference."""
    df = pd.DataFrame([row])
    if "rm_notes" not in df.columns:
        df["rm_notes"] = ""
    engineered = engineer_features(df, fit=False)
    cols = [c for c in feature_columns if c in engineered.columns]
    vec = engineered[cols].fillna(0).values[0]
    if len(vec) < len(feature_columns):
        padded = np.zeros(len(feature_columns))
        col_idx = {c: i for i, c in enumerate(feature_columns)}
        for i, c in enumerate(cols):
            padded[col_idx[c]] = vec[i]
        return padded
    return vec
