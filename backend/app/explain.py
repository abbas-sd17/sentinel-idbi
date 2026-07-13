"""SHAP-based explainability for Sentinel."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("sentinel.explain")

ML_ROOT = Path(__file__).resolve().parents[2] / "ml"
sys.path.insert(0, str(ML_ROOT))

from segments import get_reason_taxonomy  # noqa: E402

from app.scoring import REASON_DESCRIPTIONS, ScoringEngine  # noqa: E402


def _decorate(feat: str, impact: float) -> dict[str, Any]:
    """Attach description + standardized reason-code taxonomy to a feature."""
    tax = get_reason_taxonomy(feat)
    return {
        "feature": feat,
        "impact": round(float(impact), 4),
        "direction": "increases_risk" if impact > 0 else "decreases_risk",
        "description": REASON_DESCRIPTIONS.get(feat, feat.replace("_", " ").title()),
        "code": tax["code"],
        "category": tax["category"],
    }


def _permutation_importance_proxy(
    engine: ScoringEngine,
    X: np.ndarray,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Feature impact proxy: zero-out perturbation vs base prediction."""
    base_prob = float(engine.model.predict_proba(X)[0, 1])
    feature_names = engine.feature_columns
    impacts = []
    for i, feat in enumerate(feature_names):
        if i >= X.shape[1]:
            break
        perturbed = X.copy()
        perturbed[0, i] = 0.0
        perturbed_prob = float(engine.model.predict_proba(perturbed)[0, 1])
        impacts.append((feat, base_prob - perturbed_prob))

    impacts.sort(key=lambda x: abs(x[1]), reverse=True)
    return [_decorate(feat, impact) for feat, impact in impacts[:top_n]]


def explain_prediction(
    engine: ScoringEngine,
    X: np.ndarray,
    top_n: int = 5,
) -> tuple[list[dict[str, Any]], str]:
    """Generate reason codes for a prediction.

    Returns (reason_codes, method) where method is "shap" or
    "perturbation_proxy". The method is surfaced in the API response and the
    audit trail so a SHAP breakage can never silently change what the reason
    codes mean (RBI model-governance expectation: the explanation method used
    for each decision is known and recorded).
    """
    try:
        explainer = engine.get_explainer()  # built once, reused across requests
        shap_values = explainer(X)
        values = shap_values.values[0]
        if len(values.shape) > 1:
            values = values[:, 1] if values.shape[1] > 1 else values[:, 0]

        feature_names = engine.feature_columns
        impacts = list(zip(feature_names[: len(values)], values))
        impacts.sort(key=lambda x: abs(x[1]), reverse=True)
        return [_decorate(feat, impact) for feat, impact in impacts[:top_n]], "shap"
    except Exception:
        logger.warning(
            "SHAP explanation failed; falling back to perturbation proxy",
            exc_info=True,
        )
        return _permutation_importance_proxy(engine, X, top_n), "perturbation_proxy"
