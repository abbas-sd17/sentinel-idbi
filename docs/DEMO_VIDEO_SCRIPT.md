# Sentinel Demo Video Script (~2 Minutes, compact)

**Track**: IDBI Innovate 2026 - Track 04 Default Prediction Model
**Tool**: Snipping Tool / OBS screen recording, 1920x1080
**Total narration**: ~185 words — speak unhurried; the video lands well under the 3-minute cap.

---

## Shot List

### [0:00 - 0:12] Problem
**Screen**: Deck slide 2 (PowerPoint slideshow)
**Narration**:
> "IDBI's current MSME model is 16 to 22 percent accurate and warns only 3 months out. Sentinel predicts default 12 months in advance — and 95 percent of the accounts it clears stay good."

### [0:12 - 0:30] Portfolio Dashboard
**Screen**: `Alt+Tab` to dashboard (`/`) — sweep KPI cards, point at SMA strip, RAG donut; click RED filter
**Narration**:
> "Twenty thousand MSME accounts, each with a calibrated probability of default, rupee exposure at risk, an ECL provision — and the RBI SMA early-stress view banks run on today."

### [0:30 - 1:00] Account Detail + Officer Decision
**Screen**: Switch to the red-account tab — gauge, chip row, scroll to reason codes (pause on PUB-01), then submit an Escalate decision with a note
**Narration**:
> "One high-risk account: its PD, rating grade, SMA category — and an IFRS-9 stage that's evidence-gated, so a model score alone never marks a performing account credit-impaired. SHAP reason codes explain why, including public-domain signals like falling electricity consumption. Then the officer decides — escalate, with a note — recorded to the same audit trail as the score."

### [1:00 - 1:15] Batch Upload
**Screen**: `/upload` → Score the High-Risk Watchlist sample; point at the validation warning if shown
**Narration**:
> "Bulk CSV scoring runs the same validation as single accounts — bad rows are reported, never silently scored."

### [1:15 - 1:35] Benchmarks
**Screen**: Dashboard benchmarks card / deck slide 11 charts
**Narration**:
> "Delivering the 90-percent intent: 95.6 percent clearance reliability, Red-tier precision double the incumbent's accuracy, and an honest held-out AUC of 0.786 — consistent across every loan type."

### [1:35 - 1:50] Architecture & Close
**Screen**: GitHub repo README, then back to dashboard
**Narration**:
> "100 percent open source — FastAPI, Next.js, Docker, AWS-portable — DPDP-safe synthetic data, full audit trail. Sentinel: 12-month early warning, explainable, human decisions on the record. Thank you."

---

## Recording Tips
- Pre-open tabs: dashboard, red account (`/account/MSME-100420`), GitHub repo; deck in slideshow
- One silent practice run of the clicks first; pause 1 second between beats for easy trimming
- Upload to YouTube (Unlisted) and paste the link in PPT Slide 13
