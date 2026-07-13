"""FastAPI application for Sentinel."""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from pydantic import ValidationError

from app.explain import explain_prediction
from app.schemas import (
    AccountInput,
    BatchPredictionResult,
    BatchRowError,
    DecisionInput,
    DecisionRecord,
    HealthResponse,
    PortfolioSummary,
    PredictionResult,
    ReasonCode,
)
from app.scoring import ScoringEngine

ML_ROOT = Path(__file__).resolve().parents[2] / "ml"
sys.path.insert(0, str(ML_ROOT))
MODEL_PATH = os.environ.get("MODEL_PATH", str(ML_ROOT / "models"))
DATA_PATH = os.environ.get("DATA_PATH", str(ML_ROOT / "data" / "msme_panel.parquet"))

# Audit trail: every scoring decision is logged (account, PD, RAG, rating,
# stage, model version, timestamp) to support the human-in-the-loop /
# auditability requirements of the RBI AI governance norms.
AUDIT_LOG_PATH = os.environ.get(
    "AUDIT_LOG_PATH", str(Path(__file__).resolve().parent / "audit.log")
)
audit_logger = logging.getLogger("sentinel.audit")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    _handler = logging.FileHandler(AUDIT_LOG_PATH)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    audit_logger.addHandler(_handler)


def _audit(event: str, **fields) -> None:
    record = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    audit_logger.info(json.dumps(record))


app = FastAPI(
    title="Sentinel - MSME Default Prediction API",
    description="IDBI Innovate 2026 Track 04 - Early Warning System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine: ScoringEngine | None = None


@app.on_event("startup")
def load_artifacts() -> None:
    global engine
    engine = ScoringEngine(MODEL_PATH, DATA_PATH)


def _to_result(
    result: dict,
    reason_codes: list[dict],
    explanation_method: str = "shap",
    imputed_fields: list[str] | None = None,
) -> PredictionResult:
    """Assemble a PredictionResult and write an audit record."""
    imputed_fields = imputed_fields or []
    _audit(
        "score",
        account_id=result["account_id"],
        pd=result["pd_score"],
        rag=result["rag_bucket"],
        rating=result["rating_grade"],
        sma=result["sma_category"],
        stage=result["ifrs9_stage"],
        explanation_method=explanation_method,
        imputed_fields=imputed_fields,
        model_version=result["model_version"],
    )
    return PredictionResult(
        account_id=result["account_id"],
        pd_score=result["pd_score"],
        pd_percent=result["pd_percent"],
        rag_bucket=result["rag_bucket"],
        segment=result["segment"],
        rating_grade=result["rating_grade"],
        rating_band=result["rating_band"],
        sma_category=result["sma_category"],
        sma_definition=result["sma_definition"],
        ifrs9_stage=result["ifrs9_stage"],
        ifrs9_basis=result["ifrs9_basis"],
        recommended_action=result["recommended_action"],
        reason_codes=[ReasonCode(**rc) for rc in reason_codes],
        explanation_method=explanation_method,
        hazard_curve=result["hazard_curve"],
        imputed_fields=imputed_fields,
        model_version=result["model_version"],
        timestamp=result["timestamp"],
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=engine is not None and engine.model_loaded,
        data_loaded=engine is not None and engine.data_loaded,
        version="1.0.0-prototype",
    )


def _defaulted_fields(account: AccountInput) -> list[str]:
    """Optional input fields the caller did not supply (defaults applied).
    Surfaced so 'no adverse data provided' is never confused with 'no
    adverse events observed'."""
    return sorted(
        set(AccountInput.model_fields) - account.model_fields_set - {"account_id"}
    )


@app.post("/predict", response_model=PredictionResult)
def predict(account: AccountInput) -> PredictionResult:
    if engine is None:
        raise HTTPException(503, "Model not loaded")
    result = engine.score_account(account.model_dump())
    reason_codes, method = explain_prediction(engine, result["_X"])
    return _to_result(result, reason_codes, method, _defaulted_fields(account))


@app.post("/predict/batch", response_model=BatchPredictionResult)
async def predict_batch(file: UploadFile = File(...)) -> BatchPredictionResult:
    """Score an uploaded CSV/JSON. Every row passes the SAME Pydantic
    validation as /predict; invalid rows are skipped and reported (never
    silently scored from neutral defaults)."""
    if engine is None:
        raise HTTPException(503, "Model not loaded")
    content = await file.read()
    try:
        if file.filename and file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_json(io.BytesIO(content))
    except ValueError as exc:
        raise HTTPException(422, f"Could not parse upload: {exc}") from exc

    batch_id = uuid.uuid4().hex[:8]
    predictions: list[PredictionResult] = []
    skipped: list[BatchRowError] = []
    imputed_columns: set[str] = set()

    for i, (_, row) in enumerate(df.iterrows()):
        raw = {k: v for k, v in row.to_dict().items() if pd.notna(v)}
        try:
            account = AccountInput(**raw)
        except ValidationError as exc:
            skipped.append(
                BatchRowError(
                    row=i,
                    account_id=str(raw.get("account_id")) if raw.get("account_id") else None,
                    errors=[
                        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                        for e in exc.errors()
                    ],
                )
            )
            continue
        imputed_columns.update(_defaulted_fields(account))
        result = engine.score_account(account.model_dump())
        reason_codes, method = explain_prediction(engine, result["_X"])
        predictions.append(
            _to_result(result, reason_codes, method, _defaulted_fields(account))
        )

    warning = None
    if imputed_columns:
        warning = (
            "Columns not present in the upload were filled with neutral "
            "defaults (no adverse event assumed): "
            + ", ".join(sorted(imputed_columns))
            + ". Verify these feeds before relying on Green outcomes."
        )
    _audit(
        "batch_score",
        batch_id=batch_id,
        rows=len(predictions),
        skipped=len(skipped),
        imputed_columns=sorted(imputed_columns),
        file=file.filename,
    )
    return BatchPredictionResult(
        predictions=predictions,
        total=len(predictions),
        skipped=skipped,
        imputed_columns=sorted(imputed_columns),
        warning=warning,
    )


@app.get("/explain/{account_id}", response_model=PredictionResult)
def explain_account(account_id: str) -> PredictionResult:
    if engine is None:
        raise HTTPException(503, "Model not loaded")
    account = engine.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(404, f"Account {account_id} not found")
    result = engine.score_account(account)
    reason_codes, method = explain_prediction(engine, result["_X"], top_n=8)
    return _to_result(result, reason_codes, method)


# Human-in-the-loop decision capture: the officer's disposition of every
# model alert is recorded to the same audit trail as the score itself, so
# human decisions are auditable against model recommendations (the claim in
# ARCHITECTURE.md, now implemented). In-memory index for the demo UI;
# durable record lives in the JSONL audit log.
_decisions: dict[str, list[DecisionRecord]] = {}


@app.post("/decisions", response_model=DecisionRecord)
def record_decision(decision: DecisionInput) -> DecisionRecord:
    if engine is None:
        raise HTTPException(503, "Model not loaded")
    model_pd = None
    model_rag = None
    account = engine.get_account_by_id(decision.account_id)
    if account is not None:
        model_pd = round(float(account.get("predicted_pd", 0.0)), 4)
        model_rag = account.get("rag")
    record = DecisionRecord(
        account_id=decision.account_id,
        decision=decision.decision,
        note=decision.note,
        officer=decision.officer,
        model_pd=model_pd,
        model_rag=model_rag,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    _audit("decision", **record.model_dump())
    _decisions.setdefault(decision.account_id, []).append(record)
    return record


@app.get("/decisions/{account_id}", response_model=list[DecisionRecord])
def get_decisions(account_id: str) -> list[DecisionRecord]:
    return _decisions.get(account_id, [])


@app.get("/portfolio/summary", response_model=PortfolioSummary)
def portfolio_summary() -> PortfolioSummary:
    if engine is None:
        raise HTTPException(503, "Model not loaded")
    summary = engine.get_portfolio_summary()
    if "error" in summary:
        raise HTTPException(503, summary["error"])
    return PortfolioSummary(**summary)


@app.get("/monitoring/drift")
def monitoring_drift() -> dict:
    if engine is None:
        raise HTTPException(503, "Model not loaded")
    report = engine.get_drift_report()
    if "error" in report:
        raise HTTPException(503, report["error"])
    return report


@app.get("/portfolio/accounts")
def portfolio_accounts(
    rag: str | None = None,
    sector: str | None = None,
    search: str | None = None,
    sort_by: str = "predicted_pd",
    sort_dir: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> dict:
    if engine is None or engine._portfolio_df is None:
        raise HTTPException(503, "Portfolio data not loaded")
    # predicted_pd / rag are cached on the frame at startup - no re-inference.
    df = engine._portfolio_df

    if rag:
        df = df[df["rag"] == rag]
    if sector:
        df = df[df["sector"] == sector]
    if search:
        df = df[df["account_id"].str.contains(search, case=False, na=False)]

    allowed_sort = {"predicted_pd", "loan_amount", "account_id", "bureau_score"}
    if sort_by in allowed_sort:
        df = df.sort_values(sort_by, ascending=(sort_dir == "asc"))

    total = len(df)
    page = df.iloc[offset : offset + limit]
    cols = [
        "account_id", "loan_type", "sector", "borrower_profile",
        "enterprise_size", "loan_amount", "predicted_pd", "rag", "default_12m",
    ]
    return {"accounts": page[cols].to_dict(orient="records"), "total": total}
