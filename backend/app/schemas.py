"""Pydantic schemas for Sentinel API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AccountInput(BaseModel):
    account_id: str | None = None
    loan_type: str = "term_loan"
    borrower_profile: str = "etb"
    enterprise_size: str = "small"
    sector: str = "manufacturing"
    region: str = "west"
    loan_amount: float = Field(..., gt=0)
    tenure_months: int = Field(..., ge=1)
    interest_rate: float = Field(..., ge=0)
    vintage_months: int = Field(..., ge=0)
    collateral_coverage: float = Field(..., ge=0)
    # CIBIL-style commercial bureau scale
    bureau_score: float = Field(..., ge=300, le=900)
    turnover: float = Field(..., gt=0)
    gst_sales: float = Field(..., gt=0)
    foir: float = Field(..., ge=0, le=1)
    dpd_max_12m: int = Field(0, ge=0)
    emi_bounces_12m: int = Field(0, ge=0)
    avg_balance_trend: float = 0.0
    cc_utilization: float = Field(0.5, ge=0, le=1)
    gst_filing_delay_days: int = Field(0, ge=0)
    txn_volume_trend: float = 0.0
    cheque_returns_12m: int = Field(0, ge=0)
    min_balance_breaches_12m: int = Field(0, ge=0)
    # Public-domain / alternate data
    electricity_consumption_trend: float = Field(0.0, ge=-1, le=1)
    epfo_headcount_trend: float = Field(0.0, ge=-1, le=1)
    udyam_registered: int = Field(1, ge=0, le=1)
    rm_notes: str = ""


class ReasonCode(BaseModel):
    feature: str
    impact: float
    direction: str
    description: str
    code: str = "OTH-00"
    category: str = "Other"


class PredictionResult(BaseModel):
    model_config = {"protected_namespaces": ()}

    account_id: str
    pd_score: float
    pd_percent: float
    rag_bucket: str
    segment: str
    rating_grade: str = "G5"
    rating_band: str = "Moderate"
    sma_category: str = "Standard"
    sma_definition: str = ""
    ifrs9_stage: str = "Stage 1"
    ifrs9_basis: str = "12-month ECL"
    recommended_action: str
    reason_codes: list[ReasonCode]
    explanation_method: str = "shap"
    hazard_curve: list[dict[str, float]]
    imputed_fields: list[str] = []
    model_version: str
    timestamp: str


class BatchRowError(BaseModel):
    row: int
    account_id: str | None = None
    errors: list[str]


class BatchPredictionResult(BaseModel):
    predictions: list[PredictionResult]
    total: int
    skipped: list[BatchRowError] = []
    imputed_columns: list[str] = []
    warning: str | None = None


class DecisionInput(BaseModel):
    """Loan-officer disposition of a model alert (human-in-the-loop)."""

    account_id: str
    decision: str = Field(..., pattern="^(acknowledge|override|escalate)$")
    note: str = ""
    officer: str = Field(..., min_length=1)


class DecisionRecord(BaseModel):
    account_id: str
    decision: str
    note: str
    officer: str
    model_pd: float | None = None
    model_rag: str | None = None
    timestamp: str


class PortfolioSummary(BaseModel):
    model_config = {"protected_namespaces": ()}

    total_accounts: int
    default_rate_actual: float
    avg_pd: float
    rag_breakdown: dict[str, int]
    total_exposure: float
    exposure_at_risk: float
    exposure_by_rag: dict[str, float]
    expected_loss: float
    sma_breakdown: dict[str, int] = {}
    ifrs9_stage_breakdown: dict[str, int] = {}
    ecl_provision: float = 0.0
    ecl_method: str = ""
    sector_risk: list[dict[str, Any]]
    high_risk_accounts: list[dict[str, Any]]
    model_metrics: dict[str, Any]


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    model_loaded: bool
    data_loaded: bool
    version: str
