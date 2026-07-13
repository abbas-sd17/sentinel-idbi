# Root Dockerfile for Hugging Face Spaces (Docker SDK) — backend API.
# HF Spaces build this file at the repo root and expose app_port (7860).
# The synthetic dataset + trained model are baked into the image, so the
# Space needs no external database and gives a stable public URL.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ml/requirements.txt /app/ml/requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/ml/requirements.txt -r /app/backend/requirements.txt

COPY ml/ /app/ml/
COPY backend/ /app/backend/

ENV MODEL_PATH=/app/ml/models
ENV DATA_PATH=/app/ml/data/msme_panel.parquet
ENV PYTHONPATH=/app/ml:/app/backend
# Writable audit log location (HF Spaces filesystem is ephemeral but writable).
ENV AUDIT_LOG_PATH=/tmp/audit.log

WORKDIR /app/backend
# HF Spaces serves on 7860 by default; honor $PORT if the platform injects one.
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
