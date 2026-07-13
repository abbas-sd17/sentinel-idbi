"""Scoring engine for Sentinel."""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

# Add ml package to path
ML_ROOT = Path(__file__).resolve().parents[2] / "ml"
sys.path.insert(0, str(ML_ROOT))

from features import engineer_features, set_vectorizer  # noqa: E402
from segments import (  # noqa: E402
    assign_segment,
    get_ifrs9_stage,
    get_rag_bucket,
    get_rating_grade,
    get_recommended_action,
)

MODEL_VERSION = "1.0.0-prototype"

REASON_DESCRIPTIONS: dict[str, str] = {
    "dpd_max_12m": "Days past due in last 12 months",
    "emi_bounces_12m": "EMI bounce frequency",
    "cc_utilization": "Cash credit utilization level",
    "bureau_score": "Credit bureau score",
    "foir": "Fixed obligation to income ratio",
    "gst_filing_delay_days": "GST filing compliance delay",
    "avg_balance_trend": "Average balance trend",
    "behavioral_stress_index": "Composite behavioral stress",
    "nlp_distress_score": "NLP distress from RM notes",
    "loan_to_turnover": "Loan to turnover ratio",
    "cheque_returns_12m": "Cheque return incidents",
    "min_balance_breaches_12m": "Minimum balance breaches",
}


class ScoringEngine:
    """Load model artifacts and score accounts."""

    def __init__(self, model_dir: str | Path, data_path: str | Path | None = None):
        model_dir = Path(model_dir)
        self.model = joblib.load(model_dir / "model.joblib")
        self.feature_columns: list[str] = joblib.load(model_dir / "feature_columns.joblib")

        # Restore the fitted TF-IDF vocabulary BEFORE any feature engineering so
        # NLP distress scores are computed against the training vocabulary.
        vec_path = model_dir / "tfidf_vectorizer.joblib"
        if vec_path.exists():
            set_vectorizer(joblib.load(vec_path))

        self.data_path = Path(data_path) if data_path else None
        self._portfolio_df: pd.DataFrame | None = None
        self._features_df: pd.DataFrame | None = None
        self._explainer = None  # SHAP explainer, built once (lazy)

        if self.data_path and self.data_path.exists():
            self._portfolio_df = pd.read_parquet(self.data_path)
            self._features_df = engineer_features(self._portfolio_df, fit=False)
            self._prime_portfolio_cache()

    def _prime_portfolio_cache(self) -> None:
        """Score the whole portfolio once and cache PD + RAG on the frame."""
        feature_cols = [c for c in self.feature_columns if c in self._features_df.columns]
        X = self._features_df[feature_cols].fillna(0).values.astype(np.float32)
        probs = self.model.predict_proba(X)[:, 1]
        df = self._portfolio_df
        df["predicted_pd"] = probs
        df["rag"] = [get_rag_bucket(p, lt) for p, lt in zip(probs, df["loan_type"])]

    def get_explainer(self):
        """Build the SHAP explainer once and reuse it across all requests."""
        if self._explainer is None:
            import shap
            base_estimator = self.model.calibrated_classifiers_[0].estimator
            self._explainer = shap.Explainer(base_estimator)
        return self._explainer

    @property
    def model_loaded(self) -> bool:
        return self.model is not None

    @property
    def data_loaded(self) -> bool:
        return self._portfolio_df is not None

    def _build_hazard_curve(self, pd_score: float) -> list[dict[str, float]]:
        """Discrete-time hazard curve for 12-month horizon."""
        curve = []
        remaining = 1.0
        monthly_hazard = 1 - (1 - pd_score) ** (1 / 12)
        for month in range(1, 13):
            hazard = monthly_hazard * (1 + 0.02 * (month - 6) / 6)
            hazard = min(hazard, remaining)
            curve.append({"month": month, "hazard": round(hazard, 4), "cumulative_pd": round(1 - remaining + hazard, 4)})
            remaining -= hazard
            remaining = max(remaining, 0)
        return curve

    def score_account(self, account: dict[str, Any]) -> dict[str, Any]:
        """Score a single account and return prediction result."""
        df = pd.DataFrame([account])
        if "account_id" not in df.columns or not df["account_id"].iloc[0]:
            df["account_id"] = f"MSME-UPLOAD-{hashlib.md5(str(account).encode()).hexdigest()[:8]}"

        engineered = engineer_features(df, fit=False)
        feature_cols = [c for c in self.feature_columns if c in engineered.columns]
        X = engineered[feature_cols].fillna(0).values.astype(np.float32)

        # Pad missing columns
        if X.shape[1] < len(self.feature_columns):
            padded = np.zeros((1, len(self.feature_columns)), dtype=np.float32)
            col_idx = {c: i for i, c in enumerate(self.feature_columns)}
            for i, c in enumerate(feature_cols):
                padded[0, col_idx[c]] = X[0, i]
            X = padded

        pd_score = float(self.model.predict_proba(X)[0, 1])
        loan_type = account.get("loan_type", "term_loan")
        rag = get_rag_bucket(pd_score, loan_type)
        segment = assign_segment(account)
        rating = get_rating_grade(pd_score)
        ifrs9 = get_ifrs9_stage(rag)

        return {
            "account_id": str(df["account_id"].iloc[0]),
            "pd_score": round(pd_score, 4),
            "pd_percent": round(pd_score * 100, 2),
            "rag_bucket": rag,
            "segment": segment,
            "rating_grade": rating["grade"],
            "rating_band": rating["band"],
            "ifrs9_stage": ifrs9["stage"],
            "ifrs9_basis": ifrs9["basis"],
            "recommended_action": get_recommended_action(rag),
            "hazard_curve": self._build_hazard_curve(pd_score),
            "model_version": MODEL_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "_X": X,
            "_engineered": engineered,
        }

    def get_portfolio_summary(self) -> dict[str, Any]:
        """Aggregate portfolio-level KPIs."""
        if self._portfolio_df is None or self._features_df is None:
            return {"error": "Portfolio data not loaded"}

        # Use the startup cache (predicted_pd / rag already on the frame).
        df = self._portfolio_df.copy()
        probs = df["predicted_pd"].values

        rag_breakdown = df["rag"].value_counts().to_dict()

        # IFRS-9 staging distribution + provisioning estimate.
        stage_map = {"green": "Stage 1", "amber": "Stage 2", "red": "Stage 3"}
        df["ifrs9_stage"] = df["rag"].map(stage_map)
        stage_breakdown = df["ifrs9_stage"].value_counts().to_dict()
        coverage = {"Stage 1": 0.01, "Stage 2": 0.08, "Stage 3": 0.45}
        ecl_provision = float(
            sum(df[df["ifrs9_stage"] == s]["loan_amount"].sum() * c for s, c in coverage.items())
        )

        total_exposure = float(df["loan_amount"].sum())
        exposure_at_risk = float(df[df["rag"] == "red"]["loan_amount"].sum())
        exposure_by_rag = {
            str(k): float(v)
            for k, v in df.groupby("rag")["loan_amount"].sum().to_dict().items()
        }
        lgd = 0.45
        expected_loss = float((df["predicted_pd"] * df["loan_amount"] * lgd).sum())

        sector_risk = (
            df.groupby("sector")
            .agg(
                avg_pd=("predicted_pd", "mean"),
                count=("account_id", "count"),
                exposure=("loan_amount", "sum"),
            )
            .reset_index()
            .sort_values("avg_pd", ascending=False)
            .to_dict(orient="records")
        )
        high_risk = (
            df[df["rag"] == "red"]
            .nlargest(10, "predicted_pd")[
                ["account_id", "sector", "loan_type", "predicted_pd", "loan_amount", "default_12m"]
            ]
            .to_dict(orient="records")
        )

        metrics_path = ML_ROOT / "reports" / "metrics.json"
        model_metrics: dict[str, Any] = {}
        if metrics_path.exists():
            import json
            with open(metrics_path, encoding="utf-8") as f:
                model_metrics = json.load(f)

        return {
            "total_accounts": len(df),
            "default_rate_actual": round(float(df["default_12m"].mean()), 4),
            "avg_pd": round(float(probs.mean()), 4),
            "rag_breakdown": rag_breakdown,
            "total_exposure": round(total_exposure, 2),
            "exposure_at_risk": round(exposure_at_risk, 2),
            "exposure_by_rag": {k: round(v, 2) for k, v in exposure_by_rag.items()},
            "expected_loss": round(expected_loss, 2),
            "ifrs9_stage_breakdown": {str(k): int(v) for k, v in stage_breakdown.items()},
            "ecl_provision": round(ecl_provision, 2),
            "sector_risk": sector_risk,
            "high_risk_accounts": high_risk,
            "model_metrics": model_metrics,
        }

    def get_drift_report(self) -> dict[str, Any]:
        """Illustrative PSI drift check: current portfolio (reference) vs a
        simulated stressed next-quarter population."""
        from monitoring import drift_report

        if self._portfolio_df is None or self._features_df is None:
            return {"error": "Portfolio data not loaded"}

        reference = self._portfolio_df
        rng = np.random.default_rng(2026)
        current = reference.copy()
        n = len(current)
        current["dpd_max_12m"] = (current["dpd_max_12m"] + rng.normal(6, 4, n)).clip(0, 90)
        current["cc_utilization"] = (current["cc_utilization"] + rng.normal(0.05, 0.03, n)).clip(0.05, 0.99)
        current["gst_filing_delay_days"] = (current["gst_filing_delay_days"] + rng.normal(4, 3, n)).clip(0, 90)
        current["bureau_score"] = (current["bureau_score"] - rng.normal(15, 8, n)).clip(300, 850)

        cur_features = engineer_features(current, fit=False)
        feature_cols = [c for c in self.feature_columns if c in cur_features.columns]
        Xc = cur_features[feature_cols].fillna(0).values.astype(np.float32)
        current = current.copy()
        current["predicted_pd"] = self.model.predict_proba(Xc)[:, 1]

        monitored = [
            "dpd_max_12m", "cc_utilization", "gst_filing_delay_days",
            "bureau_score", "foir", "emi_bounces_12m",
        ]
        report = drift_report(reference, current, monitored)
        report["reference_avg_pd"] = round(float(reference["predicted_pd"].mean()), 4)
        report["current_avg_pd"] = round(float(current["predicted_pd"].mean()), 4)
        return report

    def get_account_by_id(self, account_id: str) -> dict[str, Any] | None:
        if self._portfolio_df is None:
            return None
        row = self._portfolio_df[self._portfolio_df["account_id"] == account_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()
