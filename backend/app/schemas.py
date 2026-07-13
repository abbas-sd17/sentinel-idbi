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
    bureau_score: float = Field(..., ge=300, le=850)
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
    ifrs9_stage: str = "Stage 1"
    ifrs9_basis: str = "12-month ECL"
    recommended_action: str
    reason_codes: list[ReasonCode]
    hazard_curve: list[dict[str, float]]
    model_version: str
    timestamp: str


class BatchPredictionResult(BaseModel):
    predictions: list[PredictionResult]
    total: int


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
    ifrs9_stage_breakdown: dict[str, int] = {}
    ecl_provision: float = 0.0
    sector_risk: list[dict[str, Any]]
    high_risk_accounts: list[dict[str, Any]]
    model_metrics: dict[str, Any]


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    model_loaded: bool
    data_loaded: bool
    version: str
