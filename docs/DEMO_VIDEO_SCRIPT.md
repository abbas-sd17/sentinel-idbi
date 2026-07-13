# Sentinel Demo Video Script (3 Minutes)

**Track**: IDBI Innovate 2026 - Track 04 Default Prediction Model
**Tool**: Loom / OBS / QuickTime screen recording
**Resolution**: 1920x1080 preferred

---

## Shot List

### [0:00 - 0:20] Problem Statement
**Screen**: Title slide or static graphic
**Narration**:
> "IDBI Bank's current MSME default prediction model achieves only 16 to 22 percent accuracy and detects stress just 3 months before default — too late to act. We built Sentinel: an AI-powered early-warning system that predicts defaults 12 months in advance with honest, bank-grade discrimination — and, crucially, without the inflated accuracy that would raise a red flag."

### [0:20 - 0:40] Portfolio Dashboard
**Screen**: Open deployed app → Portfolio Dashboard (`/`)
**Actions**:
- Show KPI cards (Total Exposure ~₹65,500 Cr, Exposure at Risk ~₹3,000 Cr, IFRS-9 ECL Provision ~₹2,560 Cr, Avg PD 9.4%) and the held-out AUC 0.79 / KS 0.46 / Gini 0.57 header
- Point to RAG (Red/Amber/Green) distribution donut (~79% Green / 15% Amber / 6% Red — a realistic portfolio)
- Scroll sector risk chart (textiles/agri hottest)
- Use the search box and RAG filter, sort the table by Exposure
- Highlight model benchmarks panel

**Narration**:
> "This is the loan officer's portfolio view. We manage risk in rupees, not just counts: about ₹65,500 crore of exposure across 20,000 MSME accounts, of which roughly ₹3,000 crore sits in the red bucket, with an IFRS-9 expected-credit-loss provision near ₹2,560 crore. Every account is scored with a calibrated probability of default. The RAG — Red, Amber, Green — distribution mirrors a real portfolio: most accounts healthy, a small stressed bucket needing immediate attention."

### [0:40 - 1:30] Account Detail Deep-Dive
**Screen**: Click a RED or AMBER account → Account Detail page
**Actions**:
- Show PD percentage gauge
- Show RAG badge, rating grade (G1-G10) + IFRS-9 stage chips, recommended action
- Scroll through 12-month hazard curve
- Highlight SHAP reason codes with taxonomy codes (BEH-01, CMP-01, ...)
- Point to "AI advisory only" disclaimer

**Narration**:
> "Drilling into a high-risk account, the gauge shows its 12-month probability of default, alongside an internal rating grade and IFRS-9 stage. The hazard curve shows when stress is expected to materialize. SHAP reason codes — each tagged with a standardized code like BEH-01 or CMP-01 — explain WHY: delayed GST filings, high utilization, days past due. The loan officer reviews this advisory and decides. Human stays in the loop per RBI AI norms."

### [1:30 - 2:00] Batch Upload
**Screen**: Navigate to `/upload`
**Actions**:
- Click "Score now" on the **High-Risk Watchlist** sample (all red) — instant results
- Then try the **Mixed Portfolio** sample to show a green/amber/red spread
- Point to the risk summary tiles (accounts scored, red count, avg PD)

**Narration**:
> "For bulk operations, loan officers upload a CSV and score hundreds of accounts instantly. We ship three ready-to-use demo datasets — low-risk, mixed, and a high-risk watchlist. Each account gets a calibrated PD, a RAG bucket, and its top reason code."

### [2:00 - 2:20] Benchmarking
**Screen**: Back to dashboard benchmarks OR show `ml/reports/` charts
**Actions**:
- Point to AUC-ROC 0.79, KS 0.46, Gini 0.57, Brier 0.073 — all on a held-out test set
- Briefly show ROC, KS, and calibration curve images; mention 6.4-month average lead time

**Narration**:
> "We deliberately don't chase a 90-plus number — in credit risk that almost always means leakage, the exact red flag raised in the AMA. On a held-out test set our model scores AUC 0.79, KS 0.46, Gini 0.57 — squarely where real MSME models live — and it holds across every loan type. It flags 58 percent of eventual defaulters an average 6.4 months before default. A Brier score of 0.07 confirms the probabilities are genuinely well-calibrated. This is the honest, defensible result a bank validator will trust."

### [2:20 - 2:45] Architecture & Compliance
**Screen**: GitHub repo README or architecture diagram
**Actions**:
- Show repo structure (ml/, backend/, frontend/, docs/)
- Point to Docker + AWS mapping in ARCHITECTURE.md
- Mention compliance docs

**Narration**:
> "Sentinel is production-ready and 100% open source: FastAPI backend on Hugging Face Spaces, Next.js dashboard on Netlify, Dockerized and AWS-portable. All data is synthetic and DPDP-safe, with a full Model Card, PSI drift monitoring, and an audit trail. Ready for IDBI sandbox migration in Stage 2 — map columns, retrain, revalidate."

### [2:45 - 3:00] Close
**Screen**: Dashboard with logo
**Narration**:
> "Sentinel — 12-month early warning, explainable AI, built for IDBI Bank. Thank you."

---

## Recording Tips
- Use deployed URL (not localhost) for the demo
- Pre-load a RED account URL in browser tab for quick switch
- Keep mouse movements smooth and deliberate
- Upload to YouTube (unlisted) or Loom and paste link in PPT Slide 13
