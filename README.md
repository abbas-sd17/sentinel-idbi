# Sentinel - MSME Default Prediction & Early-Warning System

**IDBI Innovate 2026 | Track 04: Default Prediction Model**

Sentinel is an explainable AI system that predicts MSME loan defaults **12 months in advance**, using structured financial data, behavioral transaction patterns, and unstructured RM notes. It outputs a unified **Probability of Default (PD)**, a **RAG (Red / Amber / Green) risk bucket**, an **internal rating grade**, an **IFRS-9 stage**, and **SHAP-based reason codes** for loan officers.

> **RAG here = Red / Amber / Green** traffic-light risk buckets — not retrieval-augmented generation. There is no LLM in this system.

## Problem Solved

IDBI Bank's current default prediction model achieves only **16-22% accuracy** on imbalanced MSME portfolios and predicts stress only ~3 months ahead. Sentinel delivers:

- **12-month early-warning** horizon (flags ~58% of eventual defaulters on the watchlist an average **6.4 months** before default)
- **Bank-grade discrimination on a held-out test set** — **AUC 0.79 / KS 0.46 / Gini 0.57** — credible separation, *not* the inflated >0.90 that signals leakage (the AMA red flag)
- **Structured + behavioral + unstructured (NLP)** data fusion
- **Segment-aware**: one globally-calibrated engine + per-segment RAG thresholds + per-segment validated performance; PD masterscale rating grades (G1-G10)
- **IFRS-9 / Ind-AS 109 staging** (Stage 1/2/3) with ECL provisioning
- **Common interpretation framework**: PD + RAG + a standardized reason-code taxonomy (BEH / FIN / BUR / CMP / TXT)
- **PSI drift monitoring** + JSONL audit trail for RBI AI governance

## Model performance (held-out test, n=4,000)

| Metric | Value | Bank-grade band |
|--------|-------|-----------------|
| AUC-ROC | **0.787** | 0.75-0.85 |
| KS | **0.456** | 0.35-0.50 |
| Gini | **0.574** | 0.45-0.60 |
| PR-AUC | 0.337 | > base rate (~9.3%) |
| Recall (defaulters) | 0.755 | maximize |
| Brier | 0.073 | low (well-calibrated) |

Per-segment (held-out): Cash Credit AUC 0.810 · Equipment 0.790 · LAP 0.773 · Term Loan 0.772. In-sample/full-data AUC reads ~0.87 — we deliberately report the honest held-out figure.

## Architecture

```
ml/          → Data generation, training, evaluation, drift monitoring
backend/     → FastAPI scoring + SHAP explainability + audit trail
frontend/    → Next.js loan-officer dashboard
docs/        → Architecture, compliance, model card, data dictionary
```

## Quick Start

### 1. ML Pipeline

```bash
cd ml
pip install -r requirements.txt
python generate_data.py --n 20000
python train.py
python evaluate.py
```

### 2. Backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (full stack)

```bash
docker-compose up --build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/predict` | POST | Score single account (PD, RAG, rating, IFRS-9 stage, reason codes, hazard curve) |
| `/predict/batch` | POST | Score batch (CSV/JSON) |
| `/explain/{account_id}` | GET | SHAP reason codes with taxonomy |
| `/portfolio/summary` | GET | Portfolio KPIs, RAG breakdown, IFRS-9 staging, ECL |
| `/portfolio/accounts` | GET | Filterable/sortable account table |
| `/monitoring/drift` | GET | PSI drift report (reference vs stressed population) |

## Deployment (100% open source)

- **Backend**: Hugging Face Spaces (Docker SDK) — root `Dockerfile`, port 7860
- **Frontend**: Netlify (`netlify.toml`) — set `NEXT_PUBLIC_API_URL` to the Space URL
- Fully self-hosted alternative: `docker-compose up` on any VPS
- See `docs/DEPLOYMENT.md`

## Compliance

- Synthetic data only (DPDP-safe, no real PII)
- Explainable AI with human-in-the-loop (RBI norms), Model Card + audit trail
- MIT License — original code; all dependencies permissive open source (scikit-learn, FastAPI, SHAP, Next.js)

## Team

Track 04 submission for IDBI Innovate 2026.
