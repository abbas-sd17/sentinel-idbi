# Compliance & Regulatory Alignment

## RBI IRAC / SMA / EWS alignment (live regime)

RBI has deferred Ind-AS 109 for scheduled commercial banks, so IDBI's operative framework today is the **IRAC provisioning norms**, the **SMA-0/1/2 early-stress classification**, and the **RBI Early Warning Signals / Red-Flagged Accounts (EWS/RFA) framework**. Sentinel is built to that live regime:

- **SMA category per account**: worst SMA status touched in the trailing 12 months (Standard / SMA-0 / SMA-1 / SMA-2 / NPA), surfaced per account and as a portfolio breakdown. Labeled as a **proxy**: regulatory SMA reporting uses *current* overdue days; the trailing-12-month view is the early-warning signal available from the behavioral feed.
- **EWS signal mapping**: Sentinel's standardized reason-code taxonomy (BEH / FIN / BUR / CMP / TXT / PUB) maps naturally onto the RBI EWS signal categories — repayment behavior and account conduct (BEH), financial deterioration (FIN), bureau signals (BUR), statutory-compliance stress such as GST filing delays (CMP), qualitative/field intelligence from RM notes (TXT), and public-domain/alternate-data signals (PUB).
- **Watchlist discipline**: Amber/Red buckets function as the model-driven early-warning watchlist feeding RM review, consistent with EWS/RFA expectations of proactive identification before slippage.

## IFRS-9 / Ind-AS 109 (forward-looking readiness)

Presented as **readiness**, not as the live regime — for when Ind-AS applies to banks and for ECL-based internal management in the interim:

- **Evidence-gated staging**: Stage 3 (credit-impaired) requires **90+ DPD objective evidence**. A high model PD on a performing account maps to **Stage 2 (SICR) at most** — a score alone can never mark an account credit-impaired. On the demo book the Stage 3 count is **0 by construction**, because the scored population is the performing book (trailing DPD capped at 89).
- **ECL = PD × LGD × EAD** with a flat, disclosed, illustrative **LGD of 0.45**. Stage-2 work: collateral-adjusted, product-level LGDs from bank data.

## Data Privacy (DPDP Act 2023)

- **Stage 1**: 100% synthetic data. No real customer PII processed.
- **Stage 2**: IDBI sandbox provides anonymized/mock datasets with bank consent framework.
- No data leaves the deployment boundary without explicit authorization.

## Responsible AI (RBI direction of travel)

RBI has not issued binding AI/ML model guidelines for banks; the relevant reference points are RBI's **FREE-AI committee** (framework for responsible and ethical AI, 2024-25) as the direction of travel, the **DPDP Act 2023** (Sentinel processes no personal data — synthetic only), and the **RBI IT Outsourcing / cloud directions**, which become relevant for Stage-2 deployment on bank or cloud infrastructure.

| Principle | Sentinel Implementation |
|-------------|------------------------|
| Explainability | SHAP local reason codes mapped to a standardized taxonomy (BEH/FIN/BUR/CMP/LON/TXT/PUB) |
| Human-in-the-loop | Implemented, not just disclaimed: `POST /decisions` records the officer's disposition (acknowledge / override / escalate + note + officer name) to the same JSONL audit trail as scores; retrievable via `GET /decisions/{account_id}` |
| Audit trail | Every scoring event *and* every officer decision logged as JSONL (account, PD, RAG, rating, SMA category, IFRS-9 stage, model version, timestamp) |
| Bias testing | No protected attributes in feature set; per-segment performance monitored |
| Model governance | Model Card, versioning, PSI drift monitoring (`/monitoring/drift`, methodology demo against a simulated stressed population), champion-challenger framework planned |

## SEBI / IRDAI

Not directly applicable to default prediction (credit risk, not investment/insurance advice).

## Code Originality

- All code is original, MIT-licensed
- No plagiarized or copied proprietary code
- Open-source dependencies with compatible licenses documented

## AI Coding Tools

Built with AI-assisted development (Cursor). All generated code reviewed and customized for this specific use case.

## Deployment Security

- HTTPS enforced on production endpoints (Hugging Face Spaces / Netlify)
- CORS is open (`*`) in the Stage-1 public demo for judge access; restrict to the frontend origin in production
- No secrets in repository (environment variables only)
- 100% open-source stack (MIT/BSD); no proprietary services, no external LLM, no paid APIs
