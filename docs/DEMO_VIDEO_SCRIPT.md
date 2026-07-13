# Sentinel Demo Video Script (3 Minutes)

**Track**: IDBI Innovate 2026 - Track 04 Default Prediction Model
**Tool**: Loom / OBS / QuickTime screen recording
**Resolution**: 1920x1080 preferred

---

## Shot List

### [0:00 - 0:20] Problem Statement
**Screen**: Title slide or static graphic
**Narration**:
> "IDBI Bank's current MSME default prediction model achieves only 16 to 22 percent accuracy and detects stress just 3 months before default — too late to act. We built Sentinel: an AI early-warning system that predicts defaults 12 months in advance and delivers the intent behind the bank's 90 percent target — more than 95 of every 100 accounts it clears stay good over the next year."

### [0:20 - 0:40] Portfolio Dashboard
**Screen**: Open deployed app → Portfolio Dashboard (`/`)
**Actions**:
- Show KPI cards (total exposure, exposure at risk, ECL provision, average PD) and the held-out AUC 0.79 / KS 0.43 / Gini 0.57 header
- Point to the RAG (Red/Amber/Green) distribution donut and the RBI SMA breakdown (Standard / SMA-0/1/2)
- Scroll sector risk chart (textiles/agri hottest)
- Use the search box and RAG filter, sort the table by Exposure

**Narration**:
> "This is the loan officer's portfolio view: roughly 65,000 crore rupees of exposure across 20,000 MSME accounts, each scored with a calibrated probability of default. Risk is managed in rupees — exposure at risk and an expected-credit-loss provision computed as PD times LGD times EAD. Alongside the Red-Amber-Green buckets, every account carries its RBI SMA category — the live IRAC early-stress view banks actually run on today."

### [0:40 - 1:35] Account Detail Deep-Dive + Officer Decision
**Screen**: Click a RED or AMBER account → Account Detail page
**Actions**:
- Show PD percentage gauge
- Show RAG badge, rating grade (G1-G10), SMA category chip, and the evidence-gated IFRS-9 stage chip
- Scroll through 12-month hazard curve
- Highlight SHAP reason codes with taxonomy codes — include a public-domain code (PUB-01 electricity trend or PUB-02 EPFO headcount) alongside BEH/CMP codes
- Use the decision panel: select "Escalate", type a short note, enter officer name, submit; show the decision appearing in the account's decision history

**Narration**:
> "Drilling into a high-risk account: the gauge shows its 12-month probability of default, with an internal rating grade, its SMA category, and an IFRS-9 stage that is evidence-gated — a high model score alone can flag significant risk increase, Stage 2, but never marks a performing account credit-impaired. SHAP reason codes explain why: delayed GST filings, days past due — and public-domain signals like a falling electricity consumption trend and shrinking EPFO payroll headcount. Then the human takes over: the officer acknowledges, overrides, or escalates, with a note — and that decision is recorded to the same audit trail as the score. Human-in-the-loop, implemented, not just disclaimed."

### [1:35 - 2:00] Batch Upload
**Screen**: Navigate to `/upload`
**Actions**:
- Click "Score now" on the **High-Risk Watchlist** sample (all red) — instant results
- Then the **Mixed Portfolio** sample to show a green/amber/red spread
- Point to the risk summary tiles, and to the warning banner listing any columns backfilled with neutral defaults

**Narration**:
> "For bulk operations, officers upload a CSV and score hundreds of accounts instantly. Every row passes the same validation as a single prediction — invalid rows are skipped and reported, and if any column is missing, the system says so explicitly rather than silently assuming clean behavior."

### [2:00 - 2:25] Benchmarking
**Screen**: Dashboard benchmarks OR `ml/reports/` charts
**Actions**:
- Point to NPV 95.6%, green-clearance reliability 94.7%, Red-tier precision 40.7%
- Show AUC-ROC 0.786, KS 0.43, Gini 0.57, Brier 0.075 — all on a held-out test set
- Briefly show ROC, KS, and calibration curve images

**Narration**:
> "How does this deliver the bank's 90-percent intent? Ninety-five point six percent of accounts the model clears stay good over the next 12 months, green-tier clearance reliability is 94.7 percent at the production cuts, and precision in the Red tier is 40.7 percent — roughly twice the incumbent model's 16-to-22-percent accuracy. Ranking power is an honest AUC 0.786 and KS 0.43 on a held-out test set — the band real bank-grade MSME models achieve — and it holds across every loan type. It flags 56.9 percent of eventual defaulters on the watchlist, with an illustrative average lead of 6.4 months. These synthetic-holdout numbers validate the pipeline and will be revalidated on IDBI sandbox data in Stage 2."

### [2:25 - 2:50] Architecture & Compliance
**Screen**: GitHub repo README or architecture diagram
**Actions**:
- Show repo structure (ml/, backend/, frontend/, docs/)
- Point to Docker + AWS mapping in ARCHITECTURE.md
- Mention COMPLIANCE.md: IRAC/SMA/EWS alignment, DPDP, FREE-AI direction

**Narration**:
> "Sentinel is production-ready and 100 percent open source: FastAPI backend, Next.js dashboard, Dockerized and AWS-portable. It is built for the live RBI regime — IRAC, SMA early-stress buckets, and the Early Warning Signals framework — with IFRS-9 staging ready for when Ind-AS applies. All data is synthetic and DPDP-safe, with a full Model Card, drift monitoring, and an end-to-end audit trail covering both model scores and officer decisions. Stage 2: map the sandbox columns, plug in the public-domain feeds, retrain, revalidate."

### [2:50 - 3:00] Close
**Screen**: Dashboard with logo
**Narration**:
> "Sentinel — 12-month early warning, explainable AI, human decisions on the record. Built for IDBI Bank. Thank you."

---

## Recording Tips
- Use deployed URL (not localhost) for the demo
- Pre-load a RED account URL in browser tab for quick switch
- Keep mouse movements smooth and deliberate
- Upload to YouTube (unlisted) or Loom and paste link in PPT Slide 13
