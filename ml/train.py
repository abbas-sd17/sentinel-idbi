"""Train calibrated XGBoost default prediction model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

from features import engineer_features, get_feature_columns, get_vectorizer
from segments import SEGMENT_THRESHOLDS


def train_model(
    data_path: str | Path = "data/msme_panel.parquet",
    model_dir: str | Path = "models",
) -> dict:
    """Train and persist model artifacts."""
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)

    raw = pd.read_parquet(data_path)
    features_df = engineer_features(raw, fit=True)
    feature_cols = get_feature_columns(features_df)

    X = features_df[feature_cols].values.astype(np.float32)
    y = features_df["default_12m"].values

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, np.arange(len(y)), test_size=0.2, random_state=42, stratify=y
    )

    # Handle class imbalance INSIDE the estimator (class_weight="balanced")
    # so ranking power is preserved, then wrap in cross-validated calibration
    # WITHOUT external sample weights. cv=5 pools all training data for the
    # calibration map, so PD values reflect the TRUE prior default rate and
    # stay well-calibrated while keeping full ranking granularity (AUC/KS).
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    base_clf = HistGradientBoostingClassifier(
        max_iter=300,
        max_depth=6,
        learning_rate=0.07,
        l2_regularization=1.0,
        min_samples_leaf=25,
        class_weight="balanced",
        random_state=42,
    )

    calibrated = CalibratedClassifierCV(base_clf, method="isotonic", cv=5)
    calibrated.fit(X_train, y_train)

    # Persist artifacts
    joblib.dump(calibrated, model_path / "model.joblib")
    joblib.dump(feature_cols, model_path / "feature_columns.joblib")
    joblib.dump(SEGMENT_THRESHOLDS, model_path / "segment_thresholds.joblib")
    # Persist the fitted TF-IDF vectorizer so NLP distress scoring at inference
    # uses the SAME vocabulary as training (never re-fit on a single note).
    joblib.dump(get_vectorizer(), model_path / "tfidf_vectorizer.joblib")

    # Save test split for evaluation
    meta_cols = ["account_id", "segment", "loan_type", "default_12m"]
    if "month_to_default" in features_df.columns:
        meta_cols.append("month_to_default")
    test_meta = features_df.iloc[idx_test][meta_cols].reset_index(drop=True)
    test_probs = calibrated.predict_proba(X_test)[:, 1]
    test_meta["predicted_pd"] = test_probs
    test_meta.to_parquet(model_path / "test_predictions.parquet", index=False)

    metadata = {
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "default_rate": float(y.mean()),
        "scale_pos_weight": float(scale_pos_weight),
        "n_features": len(feature_cols),
        "feature_columns": feature_cols,
    }
    with open(model_path / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Model trained | train={len(y_train)} test={len(y_test)} features={len(feature_cols)}")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/msme_panel.parquet")
    parser.add_argument("--output", default="models")
    args = parser.parse_args()
    train_model(args.data, args.output)
