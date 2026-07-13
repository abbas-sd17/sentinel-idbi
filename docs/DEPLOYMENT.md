# Sentinel Deployment Guide (Open-Source Hosting)

Everything here runs on **open-source software and open platforms** — no
proprietary services, no paid APIs, no external LLM. Backend on **Hugging Face
Spaces** (Docker SDK), frontend on **Netlify** (or any static/Next.js host).

## Prerequisites
- Public GitHub repository (code is MIT-licensed)
- Hugging Face account (free) — backend
- Netlify account (free) — frontend
- 3-minute demo video (OBS / any open recorder)

The trained model + synthetic dataset are baked into the Docker image, so the
deployment needs **no external database** and the link stays stable.

## Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Sentinel: MSME Default Prediction - IDBI Innovate Track 04"
git remote add origin https://github.com/YOUR_USERNAME/sentinel-idbi.git
git push -u origin main
```

Ensure `ml/models/*.joblib` and `ml/data/msme_panel.parquet` are committed
(they are baked into the image).

## Step 2: Deploy Backend — Hugging Face Space (Docker)

1. https://huggingface.co/new-space → SDK: **Docker** → Blank.
2. Connect the GitHub repo (or `git push` the repo to the Space remote).
   The Space uses the repo-root **`Dockerfile`** (listens on port 7860).
3. Put the metadata frontmatter from `deploy/huggingface/README.md` at the top
   of the Space's `README.md` (sets `sdk: docker`, `app_port: 7860`).
4. The Space builds automatically. Live API:
   `https://<user>-<space>.hf.space` — Swagger at `/docs`, health at `/health`.

CORS is already open (`allow_origins=["*"]`), so the frontend can call it.

## Step 3: Deploy Frontend — Netlify

1. https://app.netlify.com → Add new site → Import from GitHub.
2. Netlify reads `netlify.toml` (base = `frontend`, `@netlify/plugin-nextjs`).
3. Set environment variable:
   - `NEXT_PUBLIC_API_URL` = your HF Space URL (e.g.
     `https://<user>-sentinel-msme-default-api.hf.space`)
4. Deploy → copy the URL (e.g. `https://sentinel-idbi.netlify.app`).

(Vercel or Cloudflare Pages work identically — same env var. Pick any.)

## Step 4: Verify End-to-End

```bash
curl https://<user>-<space>.hf.space/health
# Open the Netlify URL in a browser; the dashboard should load live data.
```

## Step 5: Record Demo Video (3 min)

Follow `docs/DEMO_VIDEO_SCRIPT.md` (use OBS Studio — open source).

## Step 6: Fill PPT & Submit

```bash
python scripts/fill_ppt.py \
  --team-name "YOUR_TEAM" \
  --leader "YOUR_NAME" \
  --github "https://github.com/YOUR_USERNAME/sentinel-idbi" \
  --demo-url "https://sentinel-idbi.netlify.app" \
  --video-url "https://youtu.be/YOUR_VIDEO"
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

## Alternative fully self-hosted option

Any VPS with Docker: `docker-compose up -d` behind nginx. 100% open-source
stack, no third-party PaaS. `render.yaml` is also kept for Render/Railway if
preferred (still just runs the same open-source Docker image).
