# EasyOCR API

High-accuracy OCR REST API using EasyOCR with HuggingFace models. Supports **NVIDIA CUDA GPUs** and **AMD ROCm GPUs** (Radeon Instinct MI25, etc.) with automatic detection and seamless CPU fallback.

## Features

- **High Accuracy:** EasyOCR with CRAFT detector for superior text detection
- **Multilingual:** European languages (English, French, German, Spanish, Italian, Portuguese)
- **Mixed Text:** Handles both printed and handwritten text
- **Hardware Smart:** 
  - Auto-detects **NVIDIA CUDA GPU** (NVIDIA GPUs)
  - Auto-detects **AMD ROCm GPU** (Radeon Instinct MI25, MI50, MI60, MI100, RX 6000/7000 series)
  - Falls back to CPU if no GPU available
- **Searchable PDFs:** Returns both JSON results and searchable PDF with invisible text layer
- **Memory Optimized:** Sequential page processing for large multi-page PDFs
- **Production Ready:** Docker containerized, health checks, structured logging

## Quick Start

### Using Docker (Recommended)

#### For NVIDIA GPUs (CUDA)

```bash
# Build the container
docker build -t easyocr-api .

# Run on CPU
docker run -p 3600:3600 easyocr-api

# Run with NVIDIA GPU (requires nvidia-docker)
docker run --gpus all -p 3600:3600 easyocr-api
```

#### For AMD GPUs (ROCm)

**See [ROCM_SETUP.md](ROCM_SETUP.md) for detailed instructions**

```bash
# Quick setup on Azure NV8as v4 VM
./setup-rocm.sh

# After reboot, verify
./verify-rocm.sh

# Build and run ROCm container
docker-compose -f docker-compose.rocm.yml build
docker-compose -f docker-compose.rocm.yml up -d

# Check logs
docker logs -f easyocr-api-rocm
```

### Using Docker Compose

#### CPU/NVIDIA GPU

```bash
# CPU mode
docker-compose up

# GPU mode (edit docker-compose.yml to uncomment deploy section)
docker-compose up
```

#### AMD ROCm GPU

```bash
# ROCm mode (Azure NV8as v4, AMD Radeon Instinct MI25)
docker-compose -f docker-compose.rocm.yml up -d
```

### Test the API

```bash
# Using the example client
python examples/ocr_client.py path/to/image.jpg

# For large PDFs with timeout
python examples/ocr_client.py large_doc.pdf --timeout 3600

# Using curl
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

| Hardware | Time per Image | Speedup |
|----------|---------------|---------|
| Apple M4 CPU | 11-12s | 1x baseline |
| Intel Xeon CPU | 15-20s | 0.6-0.8x |
| NVIDIA RTX 3060 | 2.2-2.7s | **4-5x faster** |
| NVIDIA RTX 4090 | 1.6-1.9s | **6-7x faster** |
| AWS V100 | 1.8-2.2s | **5-6x faster** |

*Tested on typical document images (A4, 300 DPI, ~3MB)*

### GPU Requirements

- **Minimum:** NVIDIA GPU with CUDA 11.0+
- **Recommended:** 4GB+ VRAM
- **Software:** nvidia-docker runtime

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Development

### Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (with auto-reload)
uvicorn app.main:app --reload --port 8000
```

### Testing

```bash
# Run the example client
python examples/ocr_client.py examples/sample_image.jpg

# Or test with curl
curl -X POST http://localhost:8000/ocr \
  -F "file=@examples/sample_image.jpg" | jq .
```

## Architecture

```
easyocr-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── ocr_engine.py     # EasyOCR wrapper with hardware detection
│   └── make_pdf.py       # Searchable PDF generation
├── examples/
│   └── ocr_client.py     # Example Python client
├── Dockerfile            # Production Docker image
├── docker-compose.yml    # Easy deployment config
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Key Components

**`app/ocr_engine.py`**
- Wraps EasyOCR with automatic hardware detection
- Detects CUDA GPU via PyTorch
- Uses CRAFT detector (most accurate)
- Lazy initialization for fast startup

**`app/main.py`**
- FastAPI application with `/ocr` endpoint
- Handles image upload and processing
- Performance logging for each request

**`app/make_pdf.py`**
- Generates searchable PDFs with invisible text layer
- Text positioning matches OCR bounding boxes

## Supported Languages

Default configuration supports:
- English (en)
- French (fr)
- German (de)
- Spanish (es)
- Italian (it)
- Portuguese (pt)

EasyOCR supports 80+ languages. To add more, modify the `languages` list in `app/ocr_engine.py:33`.

## Use Cases

✅ **Ideal for:**
- Financial documents (invoices, receipts, bank statements)
- Handwritten notes and forms
- Mixed printed/handwritten content
- Documents with complex layouts
- Multi-language documents

⚠️ **Not ideal for:**
- Very high-volume batch processing (consider simpler OCR engines)
- Real-time OCR requirements (<100ms)
- Resource-constrained environments (<2GB RAM)

## Deployment

### Docker Deployment

```bash
docker build -t easyocr-api .
docker run -d -p 8000:8000 --name ocr-service easyocr-api
```

### With GPU

```bash
# Requires nvidia-docker
docker run --gpus all -d -p 8000:8000 --name ocr-service easyocr-api
```

### Kubernetes

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: easyocr-api
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: easyocr-api
        image: easyocr-api:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1  # For GPU acceleration
```

## Troubleshooting

### Container won't start
- Check Docker logs: `docker logs <container-id>`
- Verify port 8000 is available
- Ensure sufficient memory (2GB+ recommended)

### GPU not detected
- Verify nvidia-docker is installed: `docker run --gpus all nvidia/cuda:11.0-base nvidia-smi`
- Check container was started with `--gpus all` flag
- Review logs for hardware detection messages

### OCR accuracy issues
- Check image quality (300 DPI recommended)
- Verify correct language codes are configured
- Review confidence scores in response

## License

See LICENSE file.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
