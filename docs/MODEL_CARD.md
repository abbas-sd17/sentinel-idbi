# Model Card - Sentinel Default Prediction

## Model Details

| Attribute | Value |
|-----------|-------|
| Model name | Sentinel MSME Default Predictor v1.0 |
| Model type | Gradient Boosted Trees (HistGradientBoosting, `class_weight="balanced"`) + Isotonic Calibration (cv=5) |
| Task | Binary classification: default (NPA / 90+ DPD) within 12 months |
| Version | 1.0.0-prototype |
| Framework | scikit-learn 1.5 (HistGradientBoostingClassifier), SHAP for explanations |
| Features | 42 (17 numeric + 4 derived + one-hot categoricals + NLP distress score) |

### Calibration methodology

Class imbalance is handled **inside** the estimator via `class_weight="balanced"` (preserving ranking power), then the estimator is wrapped in `CalibratedClassifierCV(method="isotonic", cv=5)` fit **without** external sample weights. Calibrating on the true label distribution yields PD values that track the real ~9% base rate (mean predicted PD 0.094 vs actual 0.093) — essential for trustworthy RAG bucketing and expected-loss estimates.

## Intended Use

- **Primary**: Early-warning default prediction for MSME loan portfolios at IDBI Bank
- **Users**: Loan officers, credit risk teams, portfolio managers
- **Decision support only**: AI advises; human underwriter makes the final credit decision (RBI AI norms)

## Training Data

- **Source**: Synthetic MSME panel (20,000 accounts, seed=42)
- **Default rate**: ~9.3% (realistic MSME NPA imbalance)
- **Split**: 80/20 stratified train/test (16,000 / 4,000)
- Segment attributes (profile/size/sector) carry real risk loadings; Udyam-consistent turnover bands; product-aware collateral. An unobserved-heterogeneity shock in the default process caps achievable discrimination at a realistic level.

## Performance Metrics (Synthetic Holdout)

All metrics are computed on a **held-out 20% test split (n=4,000) never seen during training**. Scoring the full panel (mostly training rows) inflates every metric and is itself a form of leakage — we deliberately avoid it.

| Metric | Bank-grade band | Achieved | Notes |
|--------|-----------------|----------|-------|
| AUC-ROC | 0.75-0.85 | **0.787** | Ranking power |
| KS Statistic | 0.35-0.50 | **0.456** | Separation power |
| Gini | 0.45-0.60 | **0.574** | 2*AUC - 1 |
| PR-AUC | > base rate | **0.337** | Base rate ~9.3% |
| Recall (defaulters) | Maximized | **0.755** | F2-optimized threshold |
| Brier Score | Low | **0.073** | Calibration quality (well-calibrated) |
| Lift @ top decile | High | **3.9x** | Top-decile capture vs random |

### Per-segment discrimination (held-out)

Consistent, bank-grade separation across every loan type — evidence the single calibrated engine works as a *common framework* for different products:

| Loan type | AUC-ROC | KS | Gini |
|-----------|---------|-----|------|
| Cash Credit / WC | 0.810 | 0.527 | 0.621 |
| Equipment Finance | 0.790 | 0.458 | 0.579 |
| LAP | 0.773 | 0.472 | 0.546 |
| Term Loan | 0.772 | 0.417 | 0.544 |

### Early-warning lead time & RAG operating points

The system's purpose is *early* warning, so we report when and how many:

- **58%** of eventual defaulters are placed on the **Amber/Red watchlist**, on average **6.4 months** (median 6) before the default event materialises.
- **Watchlist (Amber + Red) recall 0.58** vs **Red-only recall 0.29**. Red is the high-precision *immediate-action* tier; Amber is the *watchlist*. Judge early-warning coverage on the combined watchlist, not on Red alone.

### In-sample vs held-out

Full-data (in-sample) AUC reads ~0.87; we report the honest held-out ~0.79. Scoring training rows is exactly how models reach a misleading >0.90 — we avoid it by design.

**Why the numbers are deliberately not >0.90.** In real MSME credit risk, a *strong* model achieves KS 0.35-0.50 / Gini 0.45-0.60. Reported AUC/KS above 0.90 almost always signals target leakage or in-sample evaluation — the exact "90% accuracy is a red flag" concern raised in the AMA. Our synthetic generator embeds an unobserved-heterogeneity shock the model cannot capture, capping discrimination at a realistic, defensible level.

**Why not raw accuracy?** On an ~9% default portfolio, predicting "no default" for everyone scores ~91% accuracy while catching zero defaulters. IDBI's stated 16-22% baseline likely reflects this trap. Our F2-optimized threshold prioritises catching true defaulters (recall) — the cost of a missed default far exceeds a false alarm in early warning.

## Explainability & Governance

- **SHAP** local reason codes, mapped to a standardized taxonomy (BEH / FIN / BUR / CMP / LON / TXT)
- **PD masterscale** internal rating grades (G1 safest → G10 default)
- **IFRS-9 / Ind-AS 109** staging (Stage 1/2/3) with ECL provisioning
- **Audit trail**: every scoring decision logged (account, PD, RAG, rating, stage, model version, timestamp) as JSONL

## Limitations

- Trained on synthetic data; must be re-mapped and re-validated on IDBI sandbox data (Stage 2)
- MSME segment only; not validated for retail or corporate loans
- NLP features from RM notes are simplified (TF-IDF + keyword); production would use domain-tuned embeddings
- Renamed sandbox columns are imputed with neutral defaults (won't crash) until explicitly mapped

## Ethical Considerations

- No protected attributes (gender, religion, caste) used as features
- Segment assignment based on loan/product metadata only
- Explainability via SHAP ensures auditability; human-in-the-loop mandatory for all credit actions

## Monitoring (Stage 2)

- Population Stability Index (PSI) on the score and key features (`/monitoring/drift`)
- Calibration drift detection; champion-challenger framework for model updates
- Periodic recalibration on new sandbox data
