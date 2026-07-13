# Sentinel Deployment Guide (Open-Source Hosting)

Everything here runs on **open-source software and free hosting tiers** — no
proprietary services, no paid APIs, no external LLM. The trained model +
synthetic dataset are baked into the Docker image, so the deployment needs
**no external database** and the link stays stable.

## Live deployment (current)

| Tier | Platform | URL |
|---|---|---|
| Backend API | Render (free, Docker) | https://sentinel-api-hv1o.onrender.com |
| Frontend | Netlify (free) | https://idbitrack4.netlify.app |

> ⏱️ **Warm the backend before judging/demo**: Render's free tier sleeps after
> 15 idle minutes — open
> [sentinel-api-hv1o.onrender.com/health](https://sentinel-api-hv1o.onrender.com/health)
> once, wait ~50 seconds, and the dashboard is instant after that.

## Step 1: Backend on Render (free tier)

Render deploys straight from the repo's [`render.yaml`](../render.yaml)
Blueprint — it builds [`backend/Dockerfile`](../backend/Dockerfile) (which
honors the platform-injected `$PORT`) with the repo root as build context.

1. https://dashboard.render.com → **New + → Blueprint**.
2. Under **Public Git Repository**, paste
   `https://github.com/abbas-sd17/sentinel-idbi` → **Continue** (no GitHub
   OAuth needed for a public repo; auto-deploy on push is not available on
   this path — use **Manual sync** on the Blueprint page after pushing).
3. Name the blueprint → **Deploy Blueprint**. The `sentinel-api` free web
   service builds in ~5-10 minutes.
4. Verify: `curl https://<your-service>.onrender.com/health` →
   `{"status":"ok","model_loaded":true,"data_loaded":true}`.

CORS is already open (`allow_origins=["*"]`), so the frontend can call it.

## Step 2: Frontend on Netlify

1. https://app.netlify.com → **Add new project → Import from GitHub** → pick
   the repo. Netlify reads `netlify.toml` (base = `frontend`,
   `@netlify/plugin-nextjs`).
2. Set the environment variable **before deploying** (or redeploy after
   changing it — `NEXT_PUBLIC_*` values are baked in at build time):
   - `NEXT_PUBLIC_API_URL` = your Render URL
     (e.g. `https://sentinel-api-hv1o.onrender.com`, no trailing slash)
3. Deploy → open the site; the dashboard should load live portfolio data.

(Vercel or Cloudflare Pages work identically — same env var.)

## Alternative: Hugging Face Spaces (Docker)

The repo-root [`Dockerfile`](../Dockerfile) (port 7860) and
[`deploy/huggingface/README.md`](../deploy/huggingface/README.md) frontmatter
support running the API as an HF Docker Space. **Caveat**: HF now gates the
Docker SDK behind a paid plan on new accounts, and binary files
(`*.joblib`, `*.parquet`, `*.png`) must be pushed via Git LFS/Xet. Render is
the recommended free path.

## Verify end-to-end

```bash
curl https://sentinel-api-hv1o.onrender.com/health
# Open https://idbitrack4.netlify.app - dashboard KPIs, SMA strip, account
# detail (SMA + stage chips, decision panel), batch upload validation.
```

## Fill PPT & submit

```bash
pip install python-pptx
python scripts/fill_ppt.py   # defaults carry the final team name, leader, and links
```

## Local Development

```bash
# Backend
cd backend
PYTHONPATH=../ml:. MODEL_PATH=../ml/models DATA_PATH=../ml/data/msme_panel.parquet \
  uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Docker (full stack, fully self-hosted / open source)

```bash
docker-compose up --build
# Frontend: http://localhost:3000  |  Backend: http://localhost:8000
```

Any VPS with Docker works: `docker-compose up -d` behind nginx — 100%
open-source stack, no third-party PaaS required.
