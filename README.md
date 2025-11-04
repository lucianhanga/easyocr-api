# EasyOCR API

High-accuracy OCR REST API using EasyOCR with HuggingFace models. Supports **NVIDIA CUDA GPUs** with automatic detection and seamless CPU fallback.

## Features

- **High Accuracy:** EasyOCR with CRAFT detector for superior text detection
- **Multilingual:** European languages (English, French, German, Spanish, Italian, Portuguese)
- **Mixed Text:** Handles both printed and handwritten text
- **Hardware Smart:** 
  - Auto-detects **NVIDIA CUDA GPU** when available
  - Seamlessly falls back to CPU if no GPU detected
  - Parallel processing for multi-page PDFs (4 pages concurrently on GPU, 4 on CPU)
- **Searchable PDFs:** Returns both JSON results and searchable PDF with invisible text layer
- **Memory Optimized:** Direct image extraction from PDFs, JPEG compression
- **Production Ready:** Docker containerized, health checks, structured logging

## Quick Start

### Prerequisites

- **Docker** (recommended) or Python 3.11+
- **For GPU acceleration:** NVIDIA GPU with CUDA 11.0+ and nvidia-docker runtime

### Using Docker (Recommended)

#### CPU Mode

```bash
# Build and run on CPU
docker build -t easyocr-api .
docker run -p 3600:3600 easyocr-api

# Or use docker-compose
docker-compose -f docker-compose.cpu.yml up
```

#### GPU Mode (NVIDIA CUDA)

```bash
# Build GPU-optimized image
docker build -f Dockerfile.gpu -t easyocr-api:gpu .

# Run with NVIDIA GPU (requires nvidia-docker)
docker run --gpus all -p 3600:3600 easyocr-api:gpu

# Or use docker-compose
docker-compose -f docker-compose.gpu.yml up
```

### Local Development (Python)

For development or if you prefer running without Docker:

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
# For CPU:
pip install -r requirements.txt

# For GPU (requires CUDA toolkit on host):
pip install -r requirements.gpu.txt

# 3. Run the development server
uvicorn app.main:app --reload --port 3600

# Or use the helper script:
./run.sh
```

The application will automatically detect if a CUDA GPU is available and use it.

### How to Detect if You're on a GPU (CUDA) Environment

#### Check from Host System

```bash
# Check if NVIDIA GPU is available
nvidia-smi

# Should display GPU information if CUDA GPU is available
# Example output:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.125.06   Driver Version: 525.125.06   CUDA Version: 12.0     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  NVIDIA RTX 4090     Off  | 00000000:01:00.0  On |                  Off |
# | 30%   45C    P8    25W / 450W |    500MiB / 24564MiB |      2%      Default |
# +-------------------------------+----------------------+----------------------+

# Check if Docker can access GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

#### Check from within Python

```python
import torch

# Check if CUDA is available
if torch.cuda.is_available():
    print(f"✅ CUDA GPU is available")
    print(f"GPU Device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
else:
    print("❌ No CUDA GPU detected, using CPU")
```

#### Check via API Health Endpoint

```bash
# Start the service
docker run -p 3600:3600 easyocr-api

# Check health endpoint
curl http://localhost:3600/_health

# Response will show the device being used:
# {"status": "ok", "model": "EasyOCR", "device": "cuda"}  # GPU detected
# {"status": "ok", "model": "EasyOCR", "device": "cpu"}   # CPU fallback
```

### Test the API

```bash
# Install client dependencies (if using the Python example)
pip install requests

# Using the example client
python tools/ocr_client.py path/to/image.jpg

# For large PDFs with timeout
python tools/ocr_client.py large_doc.pdf --timeout 3600

# Using curl (no dependencies needed)
curl -X POST http://localhost:3600/ocr \
  -F "file=@image.jpg" \
  -o response.json

# View the interactive docs
open http://localhost:3600/docs
```

## API Reference

### POST /ocr

Perform OCR on an uploaded image.

**Request:**
```bash
curl -X POST http://localhost:8000/ocr \
  -F "file=@image.jpg"
```

**Response:**
```json
{
  "ocr_result": [
    {
      "text": "Hello World",
      "confidence": 0.98,
      "bbox": [[10, 20], [100, 20], [100, 40], [10, 40]]
    }
  ],
  "pdf_base64": "JVBERi0xLjQKJ..."
}
```

**Fields:**
- `text`: Recognized text
- `confidence`: Recognition confidence (0.0-1.0)
- `bbox`: Bounding box coordinates `[[x0,y0], [x1,y1], [x2,y2], [x3,y3]]` (clockwise from top-left)
- `pdf_base64`: Base64-encoded searchable PDF

### GET /_health

Health check endpoint.

```bash
curl http://localhost:8000/_health
```

**Response:**
```json
{
  "status": "ok",
  "model": "EasyOCR",
  "device": "cuda"
}
```

### GET /

API information and links.

## Performance

### Hardware Comparison

| Hardware | Time per Image | Speedup | Best Use Case |
|----------|---------------|---------|---------------|
| Apple M4 CPU | 11-12s | 1x baseline | Development, testing |
| Intel Xeon CPU | 15-20s | 0.6-0.8x | Low-volume workloads |
| NVIDIA RTX 3060 | 2.2-2.7s | **4-5x faster** | Production, medium volume |
| NVIDIA RTX 4090 | 1.6-1.9s | **6-7x faster** | High-volume production |
| AWS V100 | 1.8-2.2s | **5-6x faster** | Cloud deployment |

*Tested on typical document images (A4, 300 DPI, ~3MB)*

### CPU vs GPU Deployment

#### CPU Deployment

**When to Use:**
- Development and testing environments
- Low-volume workloads (<100 documents/day)
- Cost-sensitive deployments
- GPU not available

**Configuration:**
```bash
# Use CPU-optimized Docker image (recommended for production)
docker-compose -f docker-compose.cpu.yml up

# Or with base Dockerfile (auto-detects CPU/GPU)
docker build -t easyocr-api .
docker run -p 3600:3600 easyocr-api
```

**Performance:**
- 10-20 seconds per page
- 4 pages processed in parallel
- Memory: 2-4 GB RAM
- Best with 4+ CPU cores

#### GPU Deployment (NVIDIA CUDA)

**When to Use:**
- Production environments
- High-volume workloads (100+ documents/day)
- Real-time or near real-time processing
- Cost per document matters more than infrastructure cost

**Requirements:**
- NVIDIA GPU with CUDA 11.0+
- 4GB+ VRAM recommended
- nvidia-docker runtime installed

**Configuration:**
```bash
# Use GPU-optimized Docker image
docker-compose -f docker-compose.gpu.yml up

# Or directly
docker build -f Dockerfile.gpu -t easyocr-api:gpu .
docker run --gpus all -p 3600:3600 easyocr-api:gpu
```

**Performance:**
- 1-3 seconds per page
- 4 pages processed in parallel
- Memory: 3-5 GB VRAM + 2-3 GB RAM
- **5-10x faster than CPU**

### GPU Detection and Optimization

The application automatically detects available hardware at startup:

**Detection Logic (in `app/ocr_engine.py`):**
```python
def _detect_hardware(self) -> str:
    """Detect available hardware acceleration."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"CUDA GPU detected: {gpu_name}")
            return "cuda"
    except Exception as e:
        logger.warning(f"Error detecting CUDA: {e}")
    
    logger.info("Using CPU for inference")
    return "cpu"
```

**Startup Logs:**
```
# GPU detected:
INFO:app.ocr_engine:CUDA GPU detected: NVIDIA RTX 4090
INFO:app.ocr_engine:Initializing OCR engine: languages=['en', 'fr', 'de', 'es', 'it', 'pt'], device=cuda

# CPU fallback:
INFO:app.ocr_engine:Using CPU for inference
INFO:app.ocr_engine:Initializing OCR engine: languages=['en', 'fr', 'de', 'es', 'it', 'pt'], device=cpu
```

## Architecture

```text
easyocr-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application with /ocr endpoint
│   ├── ocr_engine.py     # EasyOCR wrapper with GPU/CPU detection
│   └── make_pdf.py       # Searchable PDF generation
├── tools/
│   └── ocr_client.py     # Python client example
├── Dockerfile            # Base image (auto-detects CPU/GPU)
├── Dockerfile.cpu        # CPU-optimized image
├── Dockerfile.gpu        # GPU-optimized image (CUDA)
├── docker-compose.yml    # Default deployment (GPU)
├── docker-compose.cpu.yml # CPU-only deployment
├── docker-compose.gpu.yml # GPU deployment (explicit)
├── requirements.txt      # Base Python dependencies
├── requirements.cpu.txt  # CPU-specific dependencies
└── requirements.gpu.txt  # GPU-specific dependencies (with CUDA)
```

### Key Components

**`app/ocr_engine.py`**

- Wraps EasyOCR with automatic hardware detection
- Detects CUDA GPU via PyTorch (`torch.cuda.is_available()`)
- Uses CRAFT detector (most accurate text detection)
- Lazy initialization for fast startup

**`app/main.py`**

- FastAPI application with `/ocr` endpoint
- Handles image upload and PDF processing
- Parallel processing (4 pages concurrently using ThreadPoolExecutor)
- Performance logging for each request
- Health check endpoint at `/_health`

**`app/make_pdf.py`**

- Generates searchable PDFs with invisible text layer
- Text positioning matches OCR bounding boxes
- JPEG compression (quality=85) to optimize output size

## Supported Languages

Default configuration supports European languages:

- English (en)
- French (fr)
- German (de)
- Spanish (es)
- Italian (it)
- Portuguese (pt)

EasyOCR supports 80+ languages. To add more, modify the `languages` list in `app/ocr_engine.py`:

```python
# Example: Add Chinese and Japanese
languages = ['en', 'ch_sim', 'ja']
```

See [EasyOCR documentation](https://github.com/JaidedAI/EasyOCR#supported-languages) for all language codes.

## Use Cases

✅ **Ideal for:**

- Financial documents (invoices, receipts, bank statements)
- Handwritten notes and forms
- Mixed printed/handwritten content
- Documents with complex layouts
- Multi-language documents
- Digitizing archives and historical documents

⚠️ **Not ideal for:**

- Very high-volume batch processing (>10,000 documents/day - consider simpler OCR engines)
- Real-time OCR requirements (<100ms response time)
- Resource-constrained environments (<2GB RAM)
- Simple printed text (Tesseract OCR may be faster on CPU)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CUDA_VISIBLE_DEVICES` | `0` | Which GPU to use (GPU mode only) |
| `NVIDIA_VISIBLE_DEVICES` | `all` | NVIDIA device visibility (GPU mode only) |

## Deployment Options

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (with auto-reload)
uvicorn app.main:app --reload --port 3600
```

### Understanding the Docker Images

This project provides **3 Dockerfiles** for different deployment scenarios:

| Dockerfile | Purpose | Use Case |
|------------|---------|----------|
| `Dockerfile` | **Base/Auto-detect** | Auto-detects GPU via PyTorch. Good for development or when hardware is uncertain. |
| `Dockerfile.cpu` | **CPU-optimized** | Production CPU deployments. Uses CPU-specific PyTorch, optimized for multi-core processing. |
| `Dockerfile.gpu` | **GPU-optimized** | Production GPU deployments. Uses CUDA-enabled PyTorch, requires NVIDIA GPU. |

**Which one to use?**
- **Development**: Use `Dockerfile` (auto-detects)
- **Production CPU**: Use `Dockerfile.cpu` with `docker-compose.cpu.yml`
- **Production GPU**: Use `Dockerfile.gpu` with `docker-compose.gpu.yml`

### Docker Deployment (CPU)

```bash
# Build
docker build -t easyocr-api .

# Run
docker run -d -p 3600:3600 --name ocr-service easyocr-api

# View logs
docker logs -f ocr-service
```

### Docker Deployment (GPU)

```bash
# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi

# Build GPU image
docker build -f Dockerfile.gpu -t easyocr-api:gpu .

# Run with GPU
docker run --gpus all -d -p 3600:3600 --name ocr-service easyocr-api:gpu

# View logs
docker logs -f ocr-service
```

### Kubernetes - CPU Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: easyocr-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: easyocr-api
  template:
    metadata:
      labels:
        app: easyocr-api
    spec:
      containers:
      - name: easyocr-api
        image: easyocr-api:latest
        ports:
        - containerPort: 3600
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /_health
            port: 3600
          initialDelaySeconds: 60
          periodSeconds: 30
```

### Kubernetes - GPU Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: easyocr-api-gpu
spec:
  replicas: 1
  selector:
    matchLabels:
      app: easyocr-api-gpu
  template:
    metadata:
      labels:
        app: easyocr-api-gpu
    spec:
      containers:
      - name: easyocr-api
        image: easyocr-api:gpu
        ports:
        - containerPort: 3600
        resources:
          requests:
            memory: "8Gi"
            nvidia.com/gpu: 1
          limits:
            memory: "16Gi"
            nvidia.com/gpu: 1
        livenessProbe:
          httpGet:
            path: /_health
            port: 3600
          initialDelaySeconds: 60
          periodSeconds: 30
      nodeSelector:
        accelerator: nvidia-gpu
```

## Troubleshooting

### Container won't start

- Check Docker logs: `docker logs <container-id>`
- Verify port 3600 is available: `lsof -i :3600` (macOS/Linux) or `netstat -ano | findstr :3600` (Windows)
- Ensure sufficient memory (2GB+ for CPU, 6GB+ for GPU)

### GPU not detected

- Verify nvidia-docker is installed: `docker run --gpus all nvidia/cuda:12.1.0-base nvidia-smi`
- Check NVIDIA drivers are installed on host: `nvidia-smi`
- Ensure container was started with `--gpus all` flag
- Review container logs for hardware detection messages: `docker logs <container-id> | grep "GPU detected"`

### Container shows "Using CPU" but GPU is available

- Check if nvidia-docker runtime is configured: `docker info | grep -i nvidia`
- Verify GPU is accessible: `docker run --gpus all nvidia/cuda:12.1.0-base nvidia-smi`
- Rebuild the GPU image: `docker build -f Dockerfile.gpu -t easyocr-api:gpu .`

### OCR accuracy issues

- Check image quality (300 DPI recommended for scanned documents)
- Verify correct language codes are configured in `app/ocr_engine.py`
- Review confidence scores in response (values < 0.7 may indicate poor quality)
- Try preprocessing images (contrast adjustment, noise reduction)

### Out of memory errors

**CPU Mode:**
- Reduce parallel page processing in `app/main.py` (change `max_workers` from 4 to 2)
- Increase Docker memory limit: `docker run --memory="6g" ...`

**GPU Mode:**
- Reduce batch size or image resolution
- Monitor VRAM usage: `nvidia-smi -l 1`
- Ensure GPU has 4GB+ VRAM available

## License

See LICENSE file.

## PDF Processing

### How PDF Processing Works

The application uses an intelligent approach to handle PDF documents:

1. **Direct Image Extraction** (preferred):
   - Extracts embedded images directly from PDF pages
   - Preserves original quality without re-rendering
   - Memory-efficient (~1GB vs >6GB for rendering)
   - Faster processing

2. **Fallback Rendering** (when no embedded images):
   - Renders pages at 150 DPI (good balance)
   - Used for text-only PDFs
   - Safe memory usage

### PDF Output

For each processed document, you can receive:

- **Searchable PDF**: PDF with invisible text layer matching OCR results
- **OCR JSON**: Structured data with text, confidence scores, and bounding boxes
- **Text extraction**: Plain text from all detected regions

### PDF Quality Settings

Default JPEG compression: **quality=85** (good balance of size and quality)

To adjust quality, modify `app/make_pdf.py`:
```python
quality=95  # Higher quality, larger files
quality=85  # Default (recommended)
quality=75  # Smaller files, lower quality
```

## Performance Tuning

### CPU Deployment Optimization

1. **Adjust parallel processing:**
   - Edit `app/main.py`, find `ThreadPoolExecutor(max_workers=4)`
   - Reduce to 2 for systems with <4 cores
   - Increase to 8 for systems with 8+ cores

2. **Environment variables:**
   ```bash
   docker run -e OMP_NUM_THREADS=4 -p 3600:3600 easyocr-api
   # Set to match your CPU core count
   ```

3. **Docker resource limits:**
   ```yaml
   resources:
     limits:
       cpus: '8'      # Max CPU cores
       memory: 8G     # Max memory
   ```

### GPU Deployment Optimization

1. **Monitor GPU utilization:**
   ```bash
   # Watch GPU usage in real-time
   nvidia-smi -l 1
   
   # GPU-Util should show activity (10-90%) during processing
   ```

2. **Multiple GPUs:**
   ```bash
   # Use specific GPU
   docker run -e CUDA_VISIBLE_DEVICES=0 --gpus all -p 3600:3600 easyocr-api:gpu
   
   # Run multiple containers on different GPUs
   docker run -e CUDA_VISIBLE_DEVICES=0 --gpus '"device=0"' -p 3601:3600 easyocr-api:gpu
   docker run -e CUDA_VISIBLE_DEVICES=1 --gpus '"device=1"' -p 3602:3600 easyocr-api:gpu
   ```

3. **Batch processing tips:**
   - EasyOCR automatically batches text recognition
   - Larger batches = better GPU utilization
   - Default settings are optimal for most cases

### Expected Performance

| Configuration | Pages/Minute | Throughput | Best For |
|---------------|--------------|------------|----------|
| CPU (4 cores) | 3-6 | ~300 pages/hour | Development, testing |
| CPU (8 cores) | 6-12 | ~600 pages/hour | Light production |
| GPU (RTX 3060) | 20-30 | ~1,500 pages/hour | Production |
| GPU (RTX 4090) | 30-40 | ~2,000 pages/hour | High-volume production |

## Monitoring and Health Checks

### Health Check Endpoint

```bash
curl http://localhost:3600/_health
```

**Response:**
```json
{
  "status": "ok",
  "model": "EasyOCR",
  "device": "cuda"  // or "cpu"
}
```

### Logging

The application provides structured logging with timestamps and severity levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages
- **ERROR**: Error messages

**View logs:**
```bash
# Docker
docker logs -f <container-name>

# Docker Compose
docker-compose logs -f

# Filter for specific messages
docker logs <container-name> | grep "GPU detected"
docker logs <container-name> | grep "ERROR"
```

**Set log level:**
```bash
# Via environment variable
docker run -e LOG_LEVEL=DEBUG -p 3600:3600 easyocr-api

# Or in docker-compose.yml:
environment:
  - LOG_LEVEL=DEBUG
```

### Performance Metrics in Logs

Each OCR request logs:
- Request method and path
- Content type
- Processing time
- Number of pages processed
- Number of OCR items found
- Response status code

Example:
```
INFO:app:Request: POST /ocr - Content-Type: multipart/form-data
INFO:app:PDF has 5 pages - processing up to 4 pages in parallel
INFO:app:Success: 142 OCR items from 5 pages
INFO:app:Response: 200
```

## Docker Image Details

### Image Sizes

- **CPU Image**: ~2-3 GB
- **GPU Image**: ~5-6 GB

### What's Included

**Both images contain:**
- Python 3.11
- FastAPI + Uvicorn
- EasyOCR with HuggingFace models
- PyMuPDF (PDF processing)
- OpenCV (image processing)
- Pillow (image manipulation)
- Pre-downloaded EasyOCR models (~140MB)

**GPU image additionally includes:**
- PyTorch with CUDA 12.1 support
- NVIDIA CUDA Runtime libraries

### Build Options

**Standard build:**
```bash
docker build -t easyocr-api .                          # CPU
docker build -f Dockerfile.gpu -t easyocr-api:gpu .    # GPU
```

**Build with custom tag:**
```bash
docker build -t myregistry/easyocr-api:v1.0 .
```

**Build without cache:**
```bash
docker build --no-cache -t easyocr-api .
```

## Advanced Configuration

### Custom Language Support

Edit `app/ocr_engine.py` to change supported languages:

```python
# Current default (line ~33)
languages = ['en', 'fr', 'de', 'es', 'it', 'pt']

# Asian languages
languages = ['en', 'ch_sim', 'ja', 'ko']

# Arabic and English
languages = ['en', 'ar']

# Single language (faster)
languages = ['en']
```

Available languages: See [EasyOCR Language Support](https://github.com/JaidedAI/EasyOCR#supported-languages)

### Image Preprocessing

For better accuracy on difficult images, consider preprocessing:

```python
import cv2

# Increase contrast
img = cv2.convertScaleAbs(img, alpha=1.5, beta=0)

# Denoise
img = cv2.fastNlMeansDenoising(img)

# Binarization (black and white)
img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)[1]
```

### API Rate Limiting

To add rate limiting, use a reverse proxy like nginx or add middleware to FastAPI:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/ocr")
@limiter.limit("10/minute")
async def ocr_endpoint(...):
    ...
```

## Example Use Cases

### 1. Invoice Processing

```bash
# Process invoice and extract structured data
curl -X POST http://localhost:3600/ocr \
  -F "file=@invoice.pdf" \
  | jq '.ocr_result[] | select(.text | test("Total|Amount")) | {text, confidence}'
```

### 2. Batch Document Processing

```python
import requests
from pathlib import Path

def process_documents(directory):
    results = []
    for pdf_file in Path(directory).glob("*.pdf"):
        with open(pdf_file, 'rb') as f:
            response = requests.post(
                'http://localhost:3600/ocr',
                files={'file': f}
            )
            results.append({
                'file': pdf_file.name,
                'ocr_result': response.json()
            })
    return results

# Process all PDFs in directory
results = process_documents('./documents')
```

### 3. Extract Text with Confidence Filtering

```python
import requests
import json

response = requests.post(
    'http://localhost:3600/ocr',
    files={'file': open('document.pdf', 'rb')}
)

# Filter for high-confidence results only
high_confidence = [
    item for item in response.json()['ocr_result']
    if item['confidence'] > 0.8
]

print(json.dumps(high_confidence, indent=2))
```

## Technical Specifications

### Supported Input Formats

- **Images**: JPG, JPEG, PNG, BMP, TIFF, GIF
- **PDFs**: Single or multi-page PDF documents
- **Maximum file size**: Limited by Docker memory allocation (default: no limit)
- **Recommended image size**: Up to 4000x4000 pixels for best performance

### Output Formats

- **JSON**: Structured OCR results with text, confidence, and bounding boxes
- **PDF**: Searchable PDF with invisible text layer
- **Base64**: PDF encoded as base64 string in JSON response

### API Limits

- **Default timeout**: 300 seconds (5 minutes) for keep-alive
- **Concurrency**: Configurable (default: 1000 concurrent connections)
- **Backlog**: 2048 connections
- **Workers**: 1 (GPU mode) to avoid VRAM conflicts, adjustable for CPU

### Memory Requirements

| Mode | Minimum | Recommended | Heavy Load |
|------|---------|-------------|------------|
| CPU | 2 GB | 4 GB | 8 GB |
| GPU | 6 GB (4GB VRAM + 2GB RAM) | 10 GB (6GB VRAM + 4GB RAM) | 16 GB (8GB VRAM + 8GB RAM) |

## Security Considerations

### Best Practices

1. **Run as non-root user** (add to Dockerfile):
   ```dockerfile
   RUN useradd -m -u 1000 ocr
   USER ocr
   ```

2. **Use environment variables for secrets**:
   ```bash
   docker run -e API_KEY=$API_KEY -p 3600:3600 easyocr-api
   ```

3. **Enable HTTPS** with reverse proxy (nginx, Traefik):
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:3600;
       }
   }
   ```

4. **Implement authentication** (add to FastAPI):
   ```python
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   
   @app.post("/ocr")
   async def ocr_endpoint(token: str = Depends(security)):
       # Verify token
       ...
   ```

5. **File validation**: The API automatically validates file types, but consider additional checks for production

## Migration and Upgrades

### Upgrading from Previous Versions

1. **Backup your data**:
   ```bash
   docker commit <container-id> easyocr-api:backup
   ```

2. **Pull or build new image**:
   ```bash
   docker build -t easyocr-api:latest .
   ```

3. **Stop old container**:
   ```bash
   docker stop <container-id>
   docker rm <container-id>
   ```

4. **Start new container**:
   ```bash
   docker run -d -p 3600:3600 --name ocr-service easyocr-api:latest
   ```

5. **Verify health**:
   ```bash
   curl http://localhost:3600/_health
   ```

## FAQ

### Q: Can I process images and PDFs in the same request?
**A:** Each request handles one file (image or PDF). For batch processing, send multiple requests.

### Q: How do I improve OCR accuracy?
**A:** 
- Use high-quality source images (300 DPI for scans)
- Ensure good contrast and lighting
- Preprocess images (denoise, binarize)
- Verify correct language codes are configured

### Q: Can I use this commercially?
**A:** Yes, but check the licenses of dependencies (EasyOCR, PyTorch, etc.)

### Q: How do I handle very large PDFs?
**A:** 
- Increase timeout: `--timeout 3600` in client
- Increase Docker memory: `--memory="8g"`
- Process in smaller batches
- Consider splitting PDFs into smaller files

### Q: Does this work with handwriting?
**A:** Yes, EasyOCR handles both printed and handwritten text, though accuracy varies with handwriting clarity.

### Q: Can I run this on ARM processors (M1/M2 Mac, Raspberry Pi)?
**A:** Yes for CPU mode. GPU mode requires NVIDIA GPU (not compatible with Apple Silicon GPUs).

### Q: How do I reduce Docker image size?
**A:** The images are optimized, but you can:
- Use CPU image (~2-3GB vs 5-6GB for GPU)
- Remove unused language models
- Use multi-stage builds (already implemented)

## Project Roadmap

Potential future enhancements:
- [ ] Support for more document types (DOCX, RTF)
- [ ] Table detection and extraction
- [ ] Form field detection
- [ ] Document classification
- [ ] REST API versioning
- [ ] WebSocket support for real-time streaming
- [ ] Cloud storage integration (S3, Azure Blob)
- [ ] Database integration for result storage
- [ ] Web UI for document upload and viewing

## Related Projects

- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - The core OCR engine
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Alternative OCR engine
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - Another high-accuracy OCR solution
- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used

## License

See LICENSE file.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
