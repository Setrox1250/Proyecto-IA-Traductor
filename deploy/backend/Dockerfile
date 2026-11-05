# Backend GPU para el pipeline ES→EN.
# La imagen base incluye PyTorch 2.8.0 con CUDA 12.8.
FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    COQUI_TOS_AGREED=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/ /app/requirements/
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/requirements/web.txt

COPY src/ /app/src/
COPY configs/ /app/configs/
COPY deploy/backend/ /app/deploy/backend/

WORKDIR /app/deploy/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
