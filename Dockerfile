# ---------------------------
# EasyOCR API with HuggingFace Models
# High-accuracy OCR for mixed printed/handwritten text
# ---------------------------
# Uses EasyOCR with CRAFT detector for high-quality text detection
# Supports: Mixed printed/handwritten text, European languages
# Auto-detects: CUDA GPU (if available) or CPU

FROM python:3.11-slim

# Install system dependencies for OpenCV and EasyOCR
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    libgl1 libgomp1 \
    libjpeg-dev zlib1g \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app /app/app

# Environment variables
ENV LOG_LEVEL=INFO

# Preload EasyOCR models at build time (downloads ~140MB of models)
# This ensures first request is fast
RUN python -c "\
import logging; \
logging.basicConfig(level=logging.INFO); \
from app.ocr_engine import OCREngine; \
print('Preloading EasyOCR models...'); \
engine = OCREngine(); \
engine._lazy_init(); \
print('✅ EasyOCR models cached')"

EXPOSE 3600

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3600/_health').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3600", "--timeout-keep-alive", "300", "--limit-concurrency", "1000", "--backlog", "2048"]
