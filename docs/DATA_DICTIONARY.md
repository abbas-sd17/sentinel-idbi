# Data Dictionary - Synthetic MSME Panel

## Overview

Synthetic panel of 20,000 MSME loan accounts for the Stage-1 prototype. Schema designed to mirror plausible IDBI sandbox feeds for seamless Stage-2 migration. Seeded (seed=42) and fully reproducible.

## Generative logic (banking realism)

The panel is generated from a latent risk process calibrated to real MSME credit patterns, so the columns are internally consistent with how a bank's book actually behaves:

- **Segment attributes drive risk.** Latent default risk carries small, realistic loadings by **borrower profile** (NTC > NTB > ETB — thin-file borrowers default more), **enterprise size** (micro > small > medium), and **sector** (textiles/agri-processing run hotter than manufacturing). These are not decorative columns; they materially move the default rate.
- **Udyam-consistent scale.** `turnover` is drawn per enterprise size to respect MSMED Act thresholds (micro <= Rs 5 Cr, small <= Rs 50 Cr, medium <= Rs 250 Cr). `loan_amount` is 6-22% of turnover, capped at Rs 15 Cr, so the book reads as a genuine MSME portfolio (~Rs 65,000 Cr, ~Rs 3.3 Cr average ticket).
- **Product-aware collateral.** `collateral_coverage` base varies by product: LAP (property) highest, then equipment finance, term loan, then cash credit (current-asset / drawing-power); some loans effectively collateral-free (CGTMSE-style).
- **Observed features are noisy proxies** of latent risk, and the default event includes an **unobserved-heterogeneity shock** (fraud, promoter issues, sudden order loss) that no feature captures — capping achievable discrimination at a realistic, non-leaky level (held-out AUC ~0.79 / KS ~0.46).
- **Trailing DPD 0-90** represents standard / SMA-0/1/2 accounts at the observation point; the label predicts slippage to NPA (90+ DPD) over the next 12 months.

## Label

| Field | Type | Description |
|-------|------|-------------|
| `default_12m` | int (0/1) | Default (NPA / 90+ DPD) within next 12 months from observation date |

## Structured Features

| Field | Type | Description |
|-------|------|-------------|
| `account_id` | string | Unique account identifier (MSME-XXXXXX) |
| `loan_type` | enum | term_loan, cash_credit, lap, equipment_finance |
| `borrower_profile` | enum | ntc (new-to-credit), ntb (new-to-bank), etb (existing-to-bank) |
| `enterprise_size` | enum | micro, small, medium (Udyam scale) |
| `sector` | enum | manufacturing, trading, services, logistics, agri_processing, textiles |
| `region` | enum | north, south, west, east, central |
| `loan_amount` | float | Sanctioned loan amount (INR), 6-22% of turnover, capped Rs 15 Cr |
| `tenure_months` | int | Loan tenure in months |
| `interest_rate` | float | Annual interest rate (%), risk-based |
| `vintage_months` | int | Months since loan disbursement |
| `collateral_coverage` | float | Collateral value / loan amount ratio (product-aware) |
| `bureau_score` | float | Credit bureau score (300-850) |
| `turnover` | float | Annual business turnover (INR), Udyam-consistent by size |
| `gst_sales` | float | GST-reported sales (INR), <= turnover |
| `foir` | float | Fixed Obligation to Income Ratio |

## Behavioral Features (12-month window)

| Field | Type | Description |
|-------|------|-------------|
| `dpd_max_12m` | int | Maximum days past due in last 12 months (0-90 = SMA buckets) |
| `emi_bounces_12m` | int | EMI bounce count |
| `avg_balance_trend` | float | Month-over-month average balance trend |
| `cc_utilization` | float | Cash credit utilization ratio (0-1) |
| `gst_filing_delay_days` | int | Average GST filing delay |
| `txn_volume_trend` | float | Transaction volume trend |
| `cheque_returns_12m` | int | Cheque return count |
| `min_balance_breaches_12m` | int | Minimum balance breach count |

## Unstructured Features

| Field | Type | Description |
|-------|------|-------------|
| `rm_notes` | string | Relationship manager visit notes (free text) |
| `nlp_distress_score` | float | Derived NLP distress score (0-1), TF-IDF + keyword fusion |

## Derived Features

| Field | Type | Description |
|-------|------|-------------|
| `loan_to_turnover` | float | Loan amount / turnover ratio |
| `gst_turnover_ratio` | float | GST sales / turnover ratio |
| `behavioral_stress_index` | float | Composite behavioral stress (0-1) |
| `segment` | string | Composite segment key (loan_type\|profile\|size) |

## Evaluation-only Fields (NOT model features)

| Field | Type | Description |
|-------|------|-------------|
| `latent_risk` | float | Ground-truth latent risk (generator internal; excluded from training) |
| `month_to_default` | int | Month (1-12) the default crystallises, else 0. Used only to compute early-warning lead time; never seen by the model |

## Schema robustness

At inference, missing raw columns are backfilled with neutral defaults, extra columns are ignored, and unseen category values become all-zero one-hots. The pipeline will not crash on schema drift — but renamed sandbox columns should be explicitly mapped (below) and the model retrained for trustworthy PDs.

## Stage-2 Sandbox Mapping

| Synthetic Field | Sandbox Source |
|-----------------|----------------|
| Structured fields | Core banking system (CBS) loan master |
| Behavioral fields | Transaction database / sandbox APIs |
| Bureau score | Credit bureau API (CIBIL etc.) |
| GST data | GSTN integration |
| RM notes | CRM / document management system |
| EPFO, electricity | Public domain / alternate data APIs |
