---
title: Sentinel MSME Default API
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Sentinel — MSME Default Prediction API (Hugging Face Space)

This Space runs the **open-source** FastAPI scoring engine for the Sentinel
MSME 12-month default early-warning system (IDBI Innovate 2026, Track 04).

**To deploy this Space:**

1. Create a new Space → SDK: **Docker** → Blank.
2. Push this repository's contents (or connect the GitHub repo) so the Space
   contains the root `Dockerfile`, `ml/`, and `backend/` folders.
3. Copy the YAML frontmatter above into the Space's own `README.md` (Spaces
   read `app_port` and metadata from there).
4. The build bakes in the synthetic dataset + trained model — no external DB.
5. Once live, the API is at `https://<user>-<space>.hf.space` with Swagger at
   `/docs` and health at `/health`.

Everything here is MIT-licensed and 100% open source (scikit-learn, FastAPI,
SHAP). No proprietary services, no external LLM, no paid APIs.
