# Model Card - Sentinel Default Prediction

## Model Details

| Attribute | Value |
|-----------|-------|
| Model name | Sentinel MSME Default Predictor v1.0 |
| Model type | Gradient Boosted Trees (HistGradientBoosting, `class_weight="balanced"`) + Isotonic Calibration (cv=5) |
| Task | Binary classification: default (NPA / 90+ DPD) within 12 months |
| Version | 1.0.0-prototype |
| Framework | scikit-learn 1.5 (HistGradientBoostingClassifier), SHAP for explanations |
| Features | 45 (20 numeric — incl. 3 public-domain — + 4 derived incl. NLP distress score + 21 one-hot categoricals) |

### Calibration methodology

Class imbalance is handled **inside** the estimator via `class_weight="balanced"` (preserving ranking power), then the estimator is wrapped in `CalibratedClassifierCV(method="isotonic", cv=5)` fit **without** external sample weights. Calibrating on the true label distribution yields PD values that track the real ~9% base rate (Brier 0.075 on the held-out test set) — essential for trustworthy RAG bucketing and expected-loss estimates.

## Intended Use

- **Primary**: Early-warning default prediction for MSME loan portfolios at IDBI Bank
- **Users**: Loan officers, credit risk teams, portfolio managers
- **Decision support only**: AI advises; human underwriter makes the final credit decision, and that disposition is recorded to the audit trail (consistent with the direction of RBI's FREE-AI committee on responsible AI)

## Training Data

- **Source**: Synthetic MSME panel (20,000 accounts, seed=42)
- **Default rate**: ~9.4% (9.45% on the held-out test set — realistic MSME NPA imbalance)
- **Split**: 64/16/20 stratified train/validation/test (12,800 / 3,200 / 4,000). The operating threshold (0.0998, F2-optimal) was selected **on the validation split**; the test set was never used for any selection decision.
- Segment attributes (profile/size/sector) carry real risk loadings; Udyam-consistent turnover bands; product-aware collateral; bureau scores on the CIBIL-style commercial 300-900 scale. An unobserved-heterogeneity shock in the default process caps achievable discrimination at a realistic level.

## Performance Metrics (synthetic held-out test set)

All metrics are computed on a **held-out 20% test split (n=4,000) never seen during training or in any selection decision**. Scoring the full panel (mostly training rows) inflates every metric and is itself a form of leakage — we deliberately avoid it.

*Caveat: these numbers validate the pipeline (no leakage, honest split, realistic difficulty) and must be revalidated on IDBI sandbox data in Stage 2.*

| Metric | Bank-grade band | Achieved | Notes |
|--------|-----------------|----------|-------|
| AUC-ROC | 0.75-0.85 | **0.7861** | Ranking power |
| KS Statistic | 0.35-0.50 | **0.4317** | Separation power |
| Gini | 0.45-0.60 | **0.5723** | 2*AUC - 1 |
| PR-AUC | > base rate | **0.3264** | Base rate 9.45% |
| Brier Score | Low | **0.075** | Calibration quality (well-calibrated) |
| Lift @ top decile | High | **3.68x** | Top-decile capture vs random |

### Operating points (threshold 0.0998, selected on validation — never on test)

| Metric | Value | Reading |
|--------|-------|---------|
| NPV | **0.9556** | More than 95 of every 100 accounts the model clears stay good over the next 12 months |
| NPV (Green tier) | **0.9471** | Green-clearance reliability at the production watchlist cuts |
| Recall (defaulters) | 0.6667 | F2-optimized: a missed default costs far more than a false alarm |
| Specificity | 0.7485 | Non-defaulters correctly not flagged |
| Precision | 0.2167 | At the operating threshold |
| Balanced accuracy | 0.7076 | Accuracy corrected for the 9.45% base rate |
| Raw accuracy | 0.7408 | Reported for completeness; uninformative alone at this imbalance |

### How Sentinel delivers the >90% intent

The intent behind the bank's >90% accuracy target is reliability a credit team can act on, and the IDBI orientation session explicitly allowed teams to "select whichever target metrics you want to follow". Sentinel delivers that intent as:

1. **NPV 95.6%** — more than 95 of every 100 accounts the model clears stay good over the next 12 months.
2. **Green-clearance reliability 94.7%** at the production watchlist cuts.
3. **Red-tier precision 40.7%** — roughly 2× the incumbent model's 16-22% accuracy.
4. **Honest ranking power** — AUC 0.786 / KS 0.43, in the band real bank-grade MSME PD models achieve.

*Technical note:* raw accuracy alone is uninformative at a ~9% default rate — a model that flags nobody scores ~91% accuracy while catching zero defaulters. That is why operating quality is reported as NPV, specificity, and recall at the deployed cuts, alongside the standard ranking metrics.

### Per-segment discrimination (synthetic held-out test set)

Consistent, bank-grade separation across every loan type — evidence the single calibrated engine works as a *common framework* for different products:

| Loan type | AUC-ROC | KS | Gini |
|-----------|---------|-----|------|
| LAP | 0.7967 | 0.4418 | 0.5934 |
| Equipment Finance | 0.7959 | 0.485 | 0.5918 |
| Cash Credit / WC | 0.7775 | 0.4419 | 0.5551 |
| Term Loan | 0.7736 | 0.4183 | 0.5471 |

### Early-warning lead time & RAG operating points

The system's purpose is *early* warning, so we report when and how many:

- **56.9%** of eventual defaulters are placed on the **Amber/Red watchlist**. Average lead time **6.4 months** (median 6.0) before the default event materialises — the flagged % is a measured holdout recall; the lead-time months are inherited from the synthetic generator's default-timing assumptions and are **ILLUSTRATIVE**, requiring revalidation on real vintage data in Stage 2.
- **Watchlist (Amber + Red) recall 0.5688** (precision 0.2334) vs **Red-only recall 0.3016** (precision 0.4071). Red is the high-precision *immediate-action* tier; Amber is the *watchlist*. Judge early-warning coverage on the combined watchlist, not on Red alone.

### In-sample vs held-out

Full-data (in-sample) scoring reads materially higher than the held-out figures; we report the honest held-out numbers. In real MSME credit risk, a *strong* model achieves KS 0.35-0.50 / Gini 0.45-0.60 on genuine holdouts — Sentinel sits inside that band. Our synthetic generator embeds an unobserved-heterogeneity shock the model cannot capture, capping discrimination at a realistic, defensible level.

## Explainability & Governance

- **SHAP** local reason codes, mapped to a standardized taxonomy (BEH / FIN / BUR / CMP / LON / TXT / PUB — the PUB codes cover the public-domain features: electricity consumption trend, EPFO headcount trend, Udyam registration)
- **PD masterscale** internal rating grades (G1 safest → G10 default)
- **RBI SMA category** per account (worst status touched in trailing 12 months — a labeled proxy, since regulatory SMA reporting uses current overdue days), aligned to IRAC / EWS
- **IFRS-9 / Ind-AS 109** staging as forward-looking readiness, **evidence-gated**: Stage 3 requires 90+ DPD objective evidence; a high model PD on a performing account maps to Stage 2 (SICR) at most. ECL = PD × LGD × EAD with flat illustrative LGD 0.45
- **Human-in-the-loop, implemented**: `POST /decisions` records the officer's disposition (acknowledge / override / escalate + note + officer name) to the same JSONL audit trail as scores; retrievable via `GET /decisions/{account_id}`
- **Audit trail**: every scoring event and officer decision logged (account, PD, RAG, rating, SMA, stage, model version, timestamp) as JSONL
- **Hazard curve**: a discrete-time survival decomposition whose cumulative 12-month PD equals the headline PD exactly

## Limitations

- Trained on synthetic data; must be re-mapped and re-validated on IDBI sandbox data (Stage 2)
- MSME segment only; not validated for retail or corporate loans
- NLP features from RM notes remain a simplified proof-of-concept on synthetic notes (TF-IDF + keyword); normalization constants are frozen at fit time so single-account and batch scoring produce identical scores (train/serve consistency). Production would use domain-tuned embeddings
- Public-domain features (electricity, EPFO, Udyam) are synthetic proxies today; Stage-2 sources are state discom feeds, the EPFO API, and the Udyam portal
- Early-warning lead-time months are illustrative (generator timing assumptions), not measured on real vintages
- Renamed sandbox columns are imputed with neutral defaults (won't crash) until explicitly mapped; batch scoring reports every backfilled column explicitly

## Ethical Considerations

- No protected attributes (gender, religion, caste) used as features
- Segment assignment based on loan/product metadata only
- Explainability via SHAP ensures auditability; human-in-the-loop mandatory for all credit actions

## Monitoring (Stage 2)

- Population Stability Index (PSI) on the score and key features (`/monitoring/drift`). The Stage-1 endpoint is a methodology demo: it compares the reference portfolio against a simulated stressed population
- Calibration drift detection; champion-challenger framework for model updates
- Periodic recalibration on new sandbox data
