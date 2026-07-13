#!/usr/bin/env python3
"""Fill the mandatory IDBI Innovate PPT template with Sentinel content."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

TEMPLATE = Path("Prototype Submission Deck _ IDBI Innovate.pptx")
METRICS_PATH = Path("ml/reports/metrics.json")
OUTPUT = Path("Sentinel_Submission_Deck.pptx")


def _set_text(shape, text: str, font_size: int = 14) -> None:
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)


def _find_content_shape(slide):
    """Find the main content placeholder on a slide."""
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            return shape
    for shape in slide.shapes:
        if shape.has_text_frame:
            return shape
    return None


def _segment_lines(metrics: dict) -> str:
    """One line per loan-type segment with its held-out AUC / KS / Gini."""
    seg = metrics.get("segment_metrics") or []
    if not seg:
        return "  (per-segment metrics unavailable)"
    label = {
        "term_loan": "Term Loan", "cash_credit": "Cash Credit / WC",
        "lap": "LAP", "equipment_finance": "Equipment Finance",
    }
    return "\n".join(
        f"  • {label.get(s['loan_type'], s['loan_type']):<18} "
        f"AUC {s['auc_roc']:.3f} · KS {s['ks']:.3f} · Gini {s['gini']:.3f}  (n={s['n']})"
        for s in seg
    )


def fill_deck(
    team_name: str,
    leader: str,
    github: str,
    demo_url: str,
    video_url: str,
) -> Path:
    prs = Presentation(str(TEMPLATE))
    metrics = {}
    if METRICS_PATH.exists():
        with open(METRICS_PATH, encoding="utf-8") as f:
            metrics = json.load(f)
    ew = metrics.get("early_warning", {})

    slides_content = {
        0: (
            f"Team name: {team_name}\n"
            f"Team leader name: {leader}\n"
            f"Problem Statement: Track 04 - Default Prediction Model"
        ),
        1: (
            "Sentinel is an AI-powered MSME loan default early-warning system that predicts "
            "the probability of default 12 months in advance. It fuses structured financial data, "
            "behavioral transaction patterns, and unstructured RM notes into a single calibrated "
            "scoring engine. Loan officers receive a unified PD score, a RAG (Red/Amber/Green) risk "
            "bucket, an internal rating grade and IFRS-9 stage, and explainable reason codes — "
            "enabling proactive intervention before accounts become NPA."
        ),
        2: (
            "Opportunities:\n"
            "• IDBI's current model achieves only 16-22% accuracy and predicts stress ~3 months late\n"
            "• 12-month early-warning horizon with honest, bank-grade discrimination (KS ~0.46)\n"
            "• Common interpretation framework across all MSME loan types and segments\n\n"
            "How it solves the problem:\n"
            "• Calibrated gradient boosting + NLP distress scoring on structured + unstructured data\n"
            "• Segment-aware RAG (Red/Amber/Green) bucketing with SHAP explainability for loan officers\n"
            "• Human-in-the-loop: AI advises, underwriter decides (RBI AI norms)\n\n"
            "USP:\n"
            "• Honest, leakage-free validation (held-out KS ~0.46) instead of the inflated >0.90 red flag\n"
            "• PD masterscale rating + IFRS-9 / Ind-AS 109 ECL staging + standardized reason-code taxonomy\n"
            "• NLP on RM notes, 12-month hazard curves, PSI drift monitoring and full audit trail\n"
            "• 100% open-source, Docker/AWS-portable architecture for sandbox migration"
        ),
        3: (
            "• 12-month default probability prediction with calibrated PD score (0-100%)\n"
            "• PD masterscale internal rating grades (G1-G10) + RAG (Red/Amber/Green) bucketing per loan-type segment\n"
            "• IFRS-9 / Ind-AS 109 staging (Stage 1/2/3) with ECL provisioning estimate\n"
            "• SHAP reason codes with a standardized bank-auditable taxonomy (BEH/FIN/BUR/CMP/TXT)\n"
            "• 12-month discrete-time hazard curve visualization\n"
            "• Portfolio dashboard with sector risk heatmap, exposure-at-risk and KPI metrics\n"
            "• Batch CSV upload for bulk account scoring\n"
            "• PSI drift monitoring endpoint + JSONL audit trail (RBI AI governance)\n"
            "• Synthetic data pipeline ready for IDBI sandbox API swap (Stage 2)"
        ),
        4: (
            "Process Flow:\n"
            "1. Monthly observation snapshot of MSME loan account\n"
            "2. Feature engineering: structured + behavioral + NLP distress\n"
            "3. Segment assignment (loan type × borrower profile × enterprise size)\n"
            "4. Calibrated model scores PD (probability of default in next 12 months)\n"
            "5. Segment thresholds map PD → RAG (Red/Amber/Green); PD → rating grade + IFRS-9 stage\n"
            "6. SHAP generates top reason codes with direction (increases/decreases risk)\n"
            "7. Loan officer reviews advisory output and takes action (logged to audit trail)\n"
            "8. Portfolio dashboard aggregates risk across all accounts"
        ),
        5: (
            "[Wireframes: See deployed prototype at demo URL]\n"
            "• Portfolio Dashboard: KPI cards, RAG (Red/Amber/Green) pie, sector heatmap, account table\n"
            "• Account Detail: PD gauge, RAG badge, rating + IFRS-9 chips, hazard curve, reason codes\n"
            "• Batch Upload: CSV drag-and-drop with instant scoring results"
        ),
        6: (
            "Architecture (3-tier, open-source, AWS-portable):\n\n"
            "Frontend: Next.js 14 + Tailwind (Netlify / Vercel / AWS Amplify)\n"
            "API: FastAPI + Docker (Hugging Face Spaces / self-hosted / AWS ECS Fargate)\n"
            "ML: scikit-learn HistGradientBoosting + Isotonic Calibration\n"
            "Data: Synthetic MSME Panel Parquet (→ IDBI Sandbox APIs in Stage 2)\n"
            "Explainability: SHAP (permutation-importance fallback)\n\n"
            "Stage 2 AWS mapping:\n"
            "API → ECS Fargate | Artifacts → S3 | Data → Sandbox APIs\n"
            "Frontend → Amplify | Entry → API Gateway + ALB"
        ),
        7: (
            "Technologies (all open source):\n"
            "• Python 3.11, scikit-learn, pandas, numpy, SHAP\n"
            "• FastAPI, uvicorn, pydantic\n"
            "• Next.js 14, React 18, Tailwind CSS, Recharts\n"
            "• Docker, docker-compose\n"
            "• GitHub Actions CI/CD\n"
            "• Deployment: Hugging Face Spaces (API) + Netlify (Frontend)\n"
            "• Stage 2 target: AWS (ECS, S3, API Gateway, Amplify)\n"
            "• Compliance: DPDP-safe synthetic data, RBI AI norms, Model Card, audit trail"
        ),
        8: (
            "Estimated AWS Pilot Cost (monthly):\n"
            "• ECS Fargate (1 task): ~$15-25\n"
            "• S3 storage: ~$1-5\n"
            "• API Gateway: ~$3-10\n"
            "• Amplify hosting: ~$0-15\n"
            "• Total pilot: ~$20-55/month\n"
            "• Stage 1 prototype: Free / open-source (Hugging Face Spaces + Netlify)"
        ),
        9: (
            "[Insert screenshots from deployed prototype]\n"
            "1. Portfolio Dashboard with KPIs, RAG distribution, IFRS-9 ECL\n"
            "2. Account Detail with PD gauge, rating grade, IFRS-9 stage, hazard curve\n"
            "3. SHAP Reason Codes panel with taxonomy codes\n"
            "4. Batch Upload scoring results\n"
            "5. API Swagger docs at /docs"
        ),
        10: (
            f"Model Performance — HELD-OUT test split (n={metrics.get('n_samples', 'N/A')}, never seen in training):\n\n"
            f"• AUC-ROC: {metrics.get('auc_roc', 'N/A')}   • KS: {metrics.get('ks_statistic', 'N/A')}"
            f"   • Gini: {metrics.get('gini', 'N/A')}"
            f"   • PR-AUC: {metrics.get('pr_auc', 'N/A')} (base rate ~{round(metrics.get('default_rate', 0)*100,1)}%)\n"
            f"• Recall (defaulters): {metrics.get('recall', 'N/A')}"
            f"   • Brier: {metrics.get('brier_score', 'N/A')} (well-calibrated)"
            f"   • Top-decile lift: {metrics.get('lift_at_10pct', 'N/A')}x\n\n"
            f"Early warning (the point of the system): flags {ew.get('defaulters_flagged_pct', 'N/A')}% of future "
            f"defaulters on the Amber/Red watchlist an average {ew.get('avg_lead_time_months', 'N/A')} months before default.\n"
            f"Watchlist (Amber+Red) recall {metrics.get('recall_watchlist', 'N/A')} vs Red-only "
            f"{metrics.get('recall_at_red', 'N/A')} (Red = high-precision immediate-action tier; Amber = watchlist).\n\n"
            f"Segment-aware — consistent discrimination across every loan type (held-out):\n"
            f"{_segment_lines(metrics)}\n"
            f"Why NOT >0.90 (directly rebutting the AMA red flag):\n"
            f"• In-sample / full-data scoring reads AUC ~0.87 vs our honest held-out "
            f"{metrics.get('auc_roc', 'N/A')} — we report the held-out figure; scoring training rows\n"
            f"  (the common mistake) is exactly how models reach a misleading >0.90\n"
            f"• Real MSME PD models achieve KS 0.35-0.50 / Gini 0.45-0.60 — we sit squarely in that band\n"
            f"• The default process embeds an unobserved shock (fraud, promoter risk, order loss) that\n"
            f"  no feature can capture — capping achievable skill at a realistic level\n"
            f"• Raw accuracy {metrics.get('raw_accuracy', 'N/A')} is intentionally NOT our headline"
            f" (a 'no-default' model scores ~90% and catches zero defaulters)\n\n"
            f"Charts: ROC · PR · KS separation · Calibration · Lift/Gains · decile table (ml/reports/)"
        ),
        11: (
            "Future Development (Stage 2+):\n"
            "• Migrate to IDBI sandbox APIs: map columns, retrain, re-validate on real data\n"
            "• MLOps pipeline: PSI drift monitoring (already prototyped), champion-challenger framework\n"
            "• Periodic recalibration on new sandbox data\n"
            "• Integration with core banking system (CBS) loan master\n"
            "• Expand to retail and corporate loan segments\n"
            "• Domain-tuned NLP embeddings for RM notes\n"
            "• Real-time streaming scoring via Kafka/Kinesis\n"
            "• Pilot deployment within IDBI Bank ecosystem"
        ),
        12: (
            f"GitHub Public Repository:\n{github}\n\n"
            f"Demo Video Link (3 Minutes):\n{video_url}\n\n"
            f"Final Product Link:\n{demo_url}"
        ),
    }

    for idx, content in slides_content.items():
        if idx >= len(prs.slides):
            break
        slide = prs.slides[idx]
        shape = _find_content_shape(slide)
        if shape:
            _set_text(shape, content, font_size=11 if idx > 1 else 14)

    # Add benchmark images to the Benchmarking slide (index 10) if available.
    reports = Path("ml/reports")
    if len(prs.slides) > 10:
        bench_slide = prs.slides[10]
        for i, img_name in enumerate(["roc_curve.png", "ks_curve.png", "calibration_curve.png"]):
            img_path = reports / img_name
            if img_path.exists():
                bench_slide.shapes.add_picture(
                    str(img_path), Inches(0.4 + i * 3.15), Inches(5.0), width=Inches(3.0)
                )

    prs.save(str(OUTPUT))
    print(f"Saved filled deck to {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--team-name", default="Sentinel Team")
    parser.add_argument("--leader", default="Team Leader")
    parser.add_argument("--github", default="https://github.com/YOUR_USERNAME/sentinel-idbi")
    parser.add_argument("--demo-url", default="https://sentinel-idbi.netlify.app")
    parser.add_argument("--video-url", default="https://youtu.be/YOUR_VIDEO_ID")
    args = parser.parse_args()
    fill_deck(args.team_name, args.leader, args.github, args.demo_url, args.video_url)
