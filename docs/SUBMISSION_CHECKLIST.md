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
- [ ] **PPT filled** using `scripts/fill_ppt.py` (15 slides, template unchanged)
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

### Key Metrics to Highlight (Slide 11) — held-out test set (n=4,000), leakage-free

| Metric | Value | Bank-grade band |
|--------|-------|-----------------|
| AUC-ROC | 0.787 | 0.75-0.85 |
| KS Statistic | 0.456 | 0.35-0.50 |
| Gini | 0.574 | 0.45-0.60 |
| PR-AUC | 0.337 | > base rate (~9.3%) |
| Recall (defaulters) | 0.755 | maximize |
| Brier Score | 0.073 | low (well-calibrated) |
| Lift @ top decile | 3.9x | high |
| Early-warning lead time | 6.4 months avg (58% of defaulters flagged) | — |

**Framing:** lead with "honest, held-out, bank-grade separation — not the inflated >0.90 that signals leakage (the AMA red flag). In-sample would read ~0.87; we report the held-out figure." Per-segment AUC/KS proves it holds across all four loan types.

### After Shortlisting (July 21+)

- [ ] Refine prototype for Stage 2 (July 22-31)
- [ ] Request IDBI sandbox API access
- [ ] Migrate to AWS sandbox environment
- [ ] Re-validate model on bank-provided synthetic data
- [ ] Prepare for Demo Day (August 21)

### Support

- Email: support@hacktoskill.com
- Platform: HackToSkill IDBI Innovate dashboard
