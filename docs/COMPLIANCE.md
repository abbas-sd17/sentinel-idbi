# Compliance & Regulatory Alignment

## Data Privacy (DPDP Act 2023)

- **Stage 1**: 100% synthetic data. No real customer PII processed.
- **Stage 2**: IDBI sandbox provides anonymized/mock datasets with bank consent framework.
- No data leaves the deployment boundary without explicit authorization.

## RBI AI/ML Guidelines

| Requirement | Sentinel Implementation |
|-------------|------------------------|
| Explainability | SHAP local reason codes mapped to a standardized taxonomy (BEH/FIN/BUR/CMP/LON/TXT) |
| Human-in-the-loop | All outputs are advisory; loan officer makes the final decision |
| Audit trail | Every scoring decision logged as JSONL (account, PD, RAG, rating, IFRS-9 stage, model version, timestamp) |
| Bias testing | No protected attributes in feature set; per-segment performance monitored |
| Model governance | Model Card, versioning, PSI drift monitoring (`/monitoring/drift`), champion-challenger framework planned |

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
