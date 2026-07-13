"""Population Stability Index (PSI) drift monitoring for Sentinel.

PSI is the industry-standard measure banks use to detect when a live
population has drifted away from the population a model was trained on. A
rising PSI on the score or key drivers is the trigger for re-validation /
champion-challenger in the MLOps loop (deck Slide 12).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def population_stability_index(
    expected: np.ndarray,
    actual: np.ndarray,
    bins: int = 10,
) -> float:
    """PSI between an expected (reference) and actual (current) distribution."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    # Quantile edges from the reference distribution.
    quantiles = np.linspace(0, 1, bins + 1)
    edges = np.unique(np.quantile(expected, quantiles))
    if len(edges) < 3:  # degenerate distribution
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf

    exp_pct = np.histogram(expected, bins=edges)[0] / max(len(expected), 1)
    act_pct = np.histogram(actual, bins=edges)[0] / max(len(actual), 1)
    eps = 1e-6
    exp_pct = np.clip(exp_pct, eps, None)
    act_pct = np.clip(act_pct, eps, None)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def psi_status(psi: float) -> str:
    """Standard PSI interpretation bands."""
    if psi < 0.10:
        return "stable"
    if psi < 0.25:
        return "moderate_shift"
    return "significant_shift"


def drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    features: list[str],
    score_col: str = "predicted_pd",
) -> dict:
    """Compute PSI for the score and each monitored feature."""
    report = {"features": []}
    if score_col in reference.columns and score_col in current.columns:
        p = population_stability_index(reference[score_col], current[score_col])
        report["score_psi"] = round(p, 4)
        report["score_status"] = psi_status(p)
    for f in features:
        if f in reference.columns and f in current.columns:
            p = population_stability_index(reference[f], current[f])
            report["features"].append(
                {"feature": f, "psi": round(p, 4), "status": psi_status(p)}
            )
    report["features"].sort(key=lambda x: x["psi"], reverse=True)
    return report
