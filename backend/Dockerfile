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

WORKDIR /app/backend
EXPOSE 8000

# Honor the platform-injected PORT (Render), default 8000 for local compose.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
