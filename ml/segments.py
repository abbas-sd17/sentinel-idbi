"""Segment assignment for MSME loan accounts."""

from __future__ import annotations

from typing import Any

LOAN_TYPES = ["term_loan", "cash_credit", "lap", "equipment_finance"]
BORROWER_PROFILES = ["ntc", "ntb", "etb"]
ENTERPRISE_SIZES = ["micro", "small", "medium"]

# RAG = Red / Amber / Green traffic-light risk buckets (NOT retrieval-augmented
# generation). Thresholds tuned against the calibrated PD distribution on a
# realistic ~9-11% NPA portfolio, producing a bank-like split. Secured products
# (LAP) use tighter bands; revolving credit (CC) slightly wider.
SEGMENT_THRESHOLDS = {
    "term_loan": {"red": 0.28, "amber": 0.14},
    "cash_credit": {"red": 0.30, "amber": 0.15},
    "lap": {"red": 0.26, "amber": 0.13},
    "equipment_finance": {"red": 0.28, "amber": 0.14},
    "default": {"red": 0.28, "amber": 0.14},
}


def assign_segment(row: dict[str, Any]) -> str:
    """Return composite segment key from loan metadata."""
    loan_type = row.get("loan_type", "term_loan")
    profile = row.get("borrower_profile", "etb")
    size = row.get("enterprise_size", "small")
    return f"{loan_type}|{profile}|{size}"


def get_rag_bucket(pd_score: float, loan_type: str) -> str:
    """Map PD to a RAG (Red/Amber/Green) bucket using segment thresholds."""
    thresholds = SEGMENT_THRESHOLDS.get(loan_type, SEGMENT_THRESHOLDS["default"])
    if pd_score >= thresholds["red"]:
        return "red"
    if pd_score >= thresholds["amber"]:
        return "amber"
    return "green"


# PD masterscale: monotonic internal rating grades (G1 safest .. G10 default).
MASTERSCALE = [
    ("G1", 0.010, "Very Low"), ("G2", 0.020, "Low"), ("G3", 0.035, "Low"),
    ("G4", 0.060, "Moderate"), ("G5", 0.100, "Moderate"), ("G6", 0.160, "Elevated"),
    ("G7", 0.250, "Elevated"), ("G8", 0.400, "High"), ("G9", 0.600, "High"),
    ("G10", 1.001, "Severe"),
]


def get_rating_grade(pd_score: float) -> dict[str, str]:
    """Map PD to an internal rating grade on the masterscale."""
    for grade, upper, band in MASTERSCALE:
        if pd_score < upper:
            return {"grade": grade, "band": band}
    return {"grade": "G10", "band": "Severe"}


# IFRS-9 / Ind-AS 109 staging aligned to the RAG (Red/Amber/Green) watchlist.
IFRS9_STAGES = {
    "green": {"stage": "Stage 1", "basis": "12-month ECL", "provision_coverage": 0.01},
    "amber": {"stage": "Stage 2", "basis": "Lifetime ECL (not impaired)", "provision_coverage": 0.08},
    "red": {"stage": "Stage 3", "basis": "Lifetime ECL (credit-impaired)", "provision_coverage": 0.45},
}


def get_ifrs9_stage(rag: str) -> dict[str, Any]:
    """Return IFRS-9 stage metadata for a RAG (Red/Amber/Green) bucket."""
    return IFRS9_STAGES.get(rag, IFRS9_STAGES["green"])


# Standardized reason-code taxonomy: a stable, bank-auditable code + category
# for every model feature (the "common interpretation framework").
REASON_TAXONOMY: dict[str, dict[str, str]] = {
    "dpd_max_12m": {"code": "BEH-01", "category": "Repayment Behavior"},
    "emi_bounces_12m": {"code": "BEH-02", "category": "Repayment Behavior"},
    "cheque_returns_12m": {"code": "BEH-03", "category": "Repayment Behavior"},
    "min_balance_breaches_12m": {"code": "BEH-04", "category": "Account Conduct"},
    "cc_utilization": {"code": "BEH-05", "category": "Account Conduct"},
    "avg_balance_trend": {"code": "BEH-06", "category": "Account Conduct"},
    "txn_volume_trend": {"code": "BEH-07", "category": "Account Conduct"},
    "behavioral_stress_index": {"code": "BEH-08", "category": "Composite Behavior"},
    "bureau_score": {"code": "BUR-01", "category": "Bureau"},
    "foir": {"code": "FIN-01", "category": "Financial Leverage"},
    "loan_to_turnover": {"code": "FIN-02", "category": "Financial Leverage"},
    "gst_turnover_ratio": {"code": "FIN-03", "category": "Business Activity"},
    "turnover": {"code": "FIN-04", "category": "Business Activity"},
    "gst_sales": {"code": "FIN-05", "category": "Business Activity"},
    "loan_amount": {"code": "LON-01", "category": "Loan Structure"},
    "interest_rate": {"code": "LON-02", "category": "Loan Structure"},
    "tenure_months": {"code": "LON-03", "category": "Loan Structure"},
    "collateral_coverage": {"code": "LON-04", "category": "Collateral"},
    "vintage_months": {"code": "LON-05", "category": "Relationship"},
    "gst_filing_delay_days": {"code": "CMP-01", "category": "Compliance"},
    "nlp_distress_score": {"code": "TXT-01", "category": "Unstructured / NLP"},
}


def get_reason_taxonomy(feature: str) -> dict[str, str]:
    """Return standardized reason code + category for a feature."""
    return REASON_TAXONOMY.get(feature, {"code": "OTH-00", "category": "Other"})


def get_recommended_action(rag: str) -> str:
    """Return early-warning action for loan officers."""
    actions = {
        "red": (
            "Immediate RM review: initiate restructuring discussion, "
            "enhanced monitoring weekly, collateral revaluation."
        ),
        "amber": (
            "Schedule RM call within 7 days, review cash-flow projections, "
            "monitor DPD and GST filing compliance monthly."
        ),
        "green": (
            "Standard monitoring. Continue quarterly portfolio review."
        ),
    }
    return actions.get(rag, actions["green"])
