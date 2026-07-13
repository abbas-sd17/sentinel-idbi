# Sentinel - MSME Default Prediction & Early-Warning System

**IDBI Innovate 2026 | Track 04: Default Prediction Model**

Sentinel is an explainable AI system that predicts MSME loan defaults **12 months in advance**, fusing the problem statement's three mandated input classes: **borrower behavior + bank-internal data** (financial and transaction patterns), **public-domain signals** (electricity consumption trend, EPFO payroll headcount trend, Udyam registration), and **unstructured RM notes** (NLP). It outputs a unified **Probability of Default (PD)**, a **RAG (Red / Amber / Green) risk bucket**, an **internal rating grade**, an **RBI SMA category** (live IRAC regime), an **IFRS-9 stage** (forward-looking readiness, evidence-gated), and **SHAP-based reason codes** for loan officers — with the officer's own decision captured back into the audit trail.

> **RAG here = Red / Amber / Green** traffic-light risk buckets — not retrieval-augmented generation. There is no LLM in this system.

## Live Demo

| | Link |
|---|---|
| **Dashboard (product)** | https://idbitrack4.netlify.app |
| **Scoring API** (Swagger at `/docs`) | https://sentinel-api-hv1o.onrender.com |
| **3-minute demo video** | https://youtu.be/DLrS6FQ7Jcs |

> ⏱️ **Warm the backend before judging/demo**: Render's free tier sleeps after 15 idle minutes — open [sentinel-api-hv1o.onrender.com/health](https://sentinel-api-hv1o.onrender.com/health) once, wait ~50 seconds, and the dashboard is instant after that.

## Problem Solved

IDBI Bank's current default prediction model achieves only **16-22% accuracy** on imbalanced MSME portfolios and predicts stress only ~3 months ahead. Sentinel delivers:

- **12-month early-warning** horizon (flags **56.9%** of eventual defaulters on the watchlist, average lead **6.4 months** / median 6.0 — lead-time months are inherited from the synthetic generator's timing assumptions and are *illustrative*)
- **Bank-grade discrimination on a held-out test set** — **AUC 0.786 / KS 0.43 / Gini 0.57** — squarely in the band real bank-grade MSME PD models achieve
- **Four-class data fusion**: borrower behavior + bank-internal + public-domain + unstructured (NLP) — matching the problem statement's mandated input classes
- **Segment-aware**: one globally-calibrated engine + per-segment RAG thresholds + per-segment validated performance; PD masterscale rating grades (G1-G10)
- **RBI live-regime view**: SMA-0/1/2 category per account (trailing-12-month proxy) aligned to IRAC early-stress buckets and the RBI EWS/RFA framework
- **IFRS-9 / Ind-AS 109 staging as forward-looking readiness** — evidence-gated (Stage 3 requires 90+ DPD objective evidence) — with ECL = PD × LGD × EAD
- **Common interpretation framework**: PD + RAG + a standardized reason-code taxonomy (BEH / FIN / BUR / CMP / LON / TXT / PUB)
- **Human-in-the-loop, implemented**: officer dispositions (acknowledge / override / escalate) recorded via `POST /decisions` to the same JSONL audit trail as scores
- **PSI drift monitoring** + JSONL audit trail for model governance

## How Sentinel delivers the >90% intent

The intent behind the bank's >90% accuracy target is *reliability you can act on*. Sentinel delivers that intent on the operating points that matter (the IDBI orientation session explicitly allowed teams to "select whichever target metrics you want to follow"):

1. **NPV 95.6%** — more than 95 of every 100 accounts the model clears stay good over the next 12 months.
2. **Green-clearance reliability 94.7%** at the production watchlist cuts (`npv_green`).
3. **Red-tier precision 40.7%** — roughly **2× the incumbent model's 16-22% accuracy**.
4. **Honest ranking power** — AUC 0.786 / KS 0.43, the band real bank-grade MSME PD models achieve on genuine holdouts.

*Technical note:* raw accuracy alone is uninformative at a ~9% default rate — a model that flags nobody scores ~91% accuracy while catching zero defaulters. That is why operating quality is reported as NPV, specificity, and recall at the deployed cuts, alongside the standard ranking metrics.

## Model performance (synthetic held-out test set, n=4,000)

| Metric | Value | Bank-grade band |
|--------|-------|-----------------|
| AUC-ROC | **0.7861** | 0.75-0.85 |
| KS | **0.4317** | 0.35-0.50 |
| Gini | **0.5723** | 0.45-0.60 |
| PR-AUC | 0.3264 | > base rate (9.45%) |
| NPV | **0.9556** | maximize (clearance reliability) |
| Recall (defaulters) | 0.6667 | maximize |
| Brier | 0.075 | low (well-calibrated) |

These numbers validate the pipeline (no leakage, honest split, realistic difficulty) and must be revalidated on IDBI sandbox data in Stage 2.

Per-segment (held-out): LAP AUC 0.7967 · Equipment Finance 0.7959 · Cash Credit 0.7775 · Term Loan 0.7736. In-sample/full-data scoring reads materially higher — we deliberately report the honest held-out figures. The operating threshold (0.0998) was selected on a validation split; the test set was never used for any selection.

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
| `/predict` | POST | Score single account (PD, RAG, rating, SMA category, IFRS-9 stage, reason codes, hazard curve) |
| `/predict/batch` | POST | Score batch (CSV/JSON); every row passes the same Pydantic validation as `/predict` — invalid rows are skipped and reported, and a warning lists any columns backfilled with neutral defaults |
| `/explain/{account_id}` | GET | SHAP reason codes with taxonomy |
| `/decisions` | POST | Record officer disposition (acknowledge / override / escalate + note + officer) to the JSONL audit trail |
| `/decisions/{account_id}` | GET | Retrieve decision history for an account |
| `/portfolio/summary` | GET | Portfolio KPIs, RAG breakdown, SMA breakdown, IFRS-9 staging, ECL |
| `/portfolio/accounts` | GET | Filterable/sortable account table |
| `/monitoring/drift` | GET | PSI drift report (methodology demo: reference vs simulated stressed population) |

## Deployment (100% open source)

Deployed and live:

- **Backend**: Render free tier via `render.yaml` Blueprint ([backend/Dockerfile](backend/Dockerfile), honors platform `$PORT`) → https://sentinel-api-hv1o.onrender.com
- **Frontend**: Netlify (`netlify.toml`) with `NEXT_PUBLIC_API_URL` pointing at the Render URL → https://idbitrack4.netlify.app
- Fully self-hosted alternative: `docker-compose up` on any VPS
- Hugging Face Spaces config is also included (root `Dockerfile`, port 7860) — note HF's Docker SDK now requires a paid plan on new accounts
- Full walkthrough: `docs/DEPLOYMENT.md`

## Compliance

- Synthetic data only (DPDP Act 2023-safe, no personal data processed)
- Aligned to the live RBI regime: IRAC / SMA early-stress buckets + EWS/RFA signal categories; IFRS-9 staging as forward-looking readiness
- Explainable AI with implemented human-in-the-loop decision capture, Model Card + JSONL audit trail; consistent with the direction of RBI's FREE-AI committee (framework for responsible and ethical AI)
- MIT License — original code; all dependencies permissive open source (scikit-learn, FastAPI, SHAP, Next.js)

## Team

**ax3nr1x** — Track 04 submission for IDBI Innovate 2026. Team leader: Syed Abbas Raza.
