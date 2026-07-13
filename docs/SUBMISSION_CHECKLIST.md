# IDBI Innovate 2026 - Final Submission Checklist

## Track 04: Default Prediction Model — Sentinel

### Pre-Submission (Complete All)

- [ ] **Team formed** on HackToSkill (1-4 members)
- [ ] **Track selected**: Track 04 - Default Prediction Model
- [ ] **GitHub repo** is PUBLIC with all code pushed
- [ ] **Backend deployed** and `/health` returns `{"status":"ok"}`
- [ ] **Frontend deployed** and loads portfolio dashboard
- [ ] **End-to-end verified**: dashboard → account detail → batch upload all work
- [ ] **3-minute demo video** recorded and uploaded (YouTube/Loom)
- [ ] **PPT filled** using `scripts/fill_ppt.py` (15 slides, template headings preserved by fill_ppt.py)
- [ ] **Screenshots added** to PPT Slide 10 (from deployed prototype)

### Submission on HackToSkill

1. Go to **Team Dashboard → Submission → Prototype Submission**
2. Select problem statement: **Track 04 - Default Prediction Model**
3. Fill in:
   - **Deployment Link**: `https://YOUR-FRONTEND.netlify.app` (frontend)
   - **GitHub Repo Link**: `https://github.com/YOUR_USERNAME/sentinel-idbi`
   - **Prototype PPT**: Upload `Sentinel_Submission_Deck.pptx`
4. Click **Submit**
5. Deadline: **July 13, 2026, 11:59 PM IST**

### PPT Generation Command

```bash
pip install python-pptx
python scripts/fill_ppt.py \
  --team-name "YOUR_TEAM_NAME" \
  --leader "YOUR_NAME" \
  --github "https://github.com/YOUR_USERNAME/sentinel-idbi" \
  --demo-url "https://YOUR-FRONTEND.netlify.app" \
  --video-url "https://youtu.be/YOUR_VIDEO_ID"
```

### Key Metrics to Highlight (Slide 11) — synthetic held-out test set (n=4,000), leakage-free

*Caveat: these numbers validate the pipeline (no leakage, honest split, realistic difficulty) and must be revalidated on IDBI sandbox data in Stage 2.*

| Metric | Value | Bank-grade band |
|--------|-------|-----------------|
| NPV (clearance reliability) | 0.9556 | maximize |
| Green-clearance reliability | 0.9471 | maximize |
| Red-tier precision | 0.4071 | ≈ 2× incumbent 16-22% accuracy |
| AUC-ROC | 0.7861 | 0.75-0.85 |
| KS Statistic | 0.4317 | 0.35-0.50 |
| Gini | 0.5723 | 0.45-0.60 |
| PR-AUC | 0.3264 | > base rate (9.45%) |
| Recall (defaulters) | 0.6667 | maximize |
| Brier Score | 0.075 | low (well-calibrated) |
| Lift @ top decile | 3.68x | high |
| Early-warning coverage | 56.9% of defaulters on the watchlist; avg lead 6.4 months (lead time illustrative — generator timing assumptions) | — |

**Framing:** lead with **"How Sentinel delivers the >90% intent"** — NPV 95.6% (more than 95 of every 100 cleared accounts stay good over 12 months), green-clearance reliability 94.7% at the production cuts, Red-tier precision 40.7% ≈ 2× the incumbent's 16-22% accuracy, and honest ranking power AUC 0.786 / KS 0.43 in the band real bank-grade MSME PD models achieve. The orientation session explicitly allowed teams to "select whichever target metrics you want to follow" (OrientationSessionInnovate.txt, lines 612-613). The operating threshold (0.0998) was selected on a validation split — the test set was never used for any selection. Per-segment AUC (LAP 0.7967, Equipment 0.7959, Cash Credit 0.7775, Term Loan 0.7736) proves it holds across all four loan types.

### After Shortlisting (July 21+)

- [ ] Refine prototype for Stage 2 (July 22-31)
- [ ] Request IDBI sandbox API access
- [ ] Migrate to AWS sandbox environment
- [ ] Re-validate model on bank-provided synthetic data
- [ ] Prepare for Demo Day (August 21)

### Support

- Email: support@hacktoskill.com
- Platform: HackToSkill IDBI Innovate dashboard
