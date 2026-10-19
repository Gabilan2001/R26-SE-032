# Dockerfile for app_mobile.py -- the TomatoDoc Disease module's production
# backend (single YOLOv8s model, native-640, 4-class + Gemini RAG treatment).
#
# Build context MUST be this folder (Disease_Detection/), so it can reach
# both pipeline/stage4_inference/ and models/. From this folder:
#   docker build -t disease-detection-backend .
#
# app_mobile.py resolves BASE = parents[2] of its own path, i.e. it expects
# to find itself at <BASE>/pipeline/stage4_inference/app_mobile.py and the
# models at <BASE>/models/... -- that layout is preserved below.

FROM python:3.11-slim AS base

# Minimal system libs some wheels dlopen at runtime (opencv-headless still
# wants libgomp1 for OpenMP and, despite being "headless", still links
# against libxcb at import time; onnxruntime/rembg wants libglib2.0-0).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 libglib2.0-0 libxcb1 libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/Disease_Detection

# ── Install Python deps first (own layer, cached across code-only rebuilds) ──
COPY pipeline/stage4_inference/requirements.txt pipeline/stage4_inference/requirements.txt
RUN pip install --no-cache-dir -r pipeline/stage4_inference/requirements.txt

# ── App code + knowledge base (no .env -- secrets come from Cloud Run env) ──
COPY pipeline/stage4_inference/app_mobile.py pipeline/stage4_inference/app_mobile.py
COPY pipeline/stage4_inference/rag.py pipeline/stage4_inference/rag.py
COPY pipeline/stage4_inference/ingest.py pipeline/stage4_inference/ingest.py
COPY pipeline/stage4_inference/knowledge_base.json pipeline/stage4_inference/knowledge_base.json

# ── Model weights (only the one final model -- not the 5-model research set) ──
COPY models/yolov8s_compare/weights/best.pt models/yolov8s_compare/weights/best.pt
COPY models/leaf_validator.pth models/leaf_validator.pth

# ── Build-time steps that need network access, baked into the image so the
#    container never needs outbound downloads at request time ──
# 1) Vector DB: chunk knowledge_base.json + embed with sentence-transformers.
#    This also caches the all-MiniLM-L6-v2 model under /root/.cache/huggingface.
RUN cd pipeline/stage4_inference && python ingest.py

# 2) Pre-warm rembg's background-removal model (u2net) so the FIRST real
#    request doesn't pay a slow first-time download.
RUN python -c "from rembg import remove; from PIL import Image; import numpy as np; \
    remove(Image.fromarray(np.zeros((32, 32, 3), dtype='uint8')))"

# Cloud Run injects $PORT (defaults to 8080) -- gunicorn binds to it directly,
# bypassing app_mobile.py's own `app.run(port=5002)` (that only fires when
# run directly with `python app_mobile.py`, e.g. for local testing).
ENV PORT=8080
EXPOSE 8080

WORKDIR /app/Disease_Detection/pipeline/stage4_inference

# Single worker: the YOLO + leaf-validator + embedder models are loaded once
# at import time: multiple gunicorn workers would each load their own copy
# and multiply memory use. --threads lets that one worker still handle a
# couple of concurrent requests. --timeout well above the measured ~90s
# worst case (multi-disease RAG answers).
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 300 app_mobile:app"]
