# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready OCR REST API built with FastAPI and EasyOCR. It provides high-accuracy text recognition with automatic GPU/CPU hardware detection and returns both JSON results and searchable PDFs. The API specializes in European multilingual text (printed and handwritten) including financial documents.

## Development Commands

### Local Development
```bash
# Quick start (creates venv, installs deps, runs server)
./run.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3600
```

### Docker
```bash
# Build
docker build -t easyocr-api .

# Run CPU mode
docker run -p 3600:3600 easyocr-api
# Or: docker-compose up

# Run GPU mode (requires nvidia-docker)
docker run --gpus all -p 3600:3600 easyocr-api
# Or: docker-compose -f docker-compose.gpu.yml up
```

### Testing
```bash
# Generate test image
python examples/create_sample_image.py sample.png

# Test with Python client
python examples/ocr_client.py sample.png

# Test with curl
curl -X POST http://localhost:3600/ocr -F "file=@sample.png" -o response.json

# Check health
curl http://localhost:3600/_health
```

## Architecture

### Core Application Structure

**app/main.py** - FastAPI application with three endpoints:
- `POST /ocr` - Main OCR endpoint (accepts image upload, returns JSON + PDF)
- `GET /_health` - Health check with device info
- `GET /` - API information

**app/ocr_engine.py** - OCR engine wrapper with:
- Hardware detection via `torch.cuda.is_available()` at initialization
- Lazy initialization pattern - EasyOCR reader loads on first request
- Uses CRAFT detector (most accurate for mixed text)
- Returns standardized format: `[bbox, (text, confidence)]`

**app/make_pdf.py** - PDF generation:
- Creates searchable PDFs with invisible text layer over original image
- Text positioning matches OCR bounding boxes
- Returns base64-encoded PDF bytes

### Key Design Patterns

**Lazy Initialization**: The OCR model (app/main.py:32) is initialized as `None` and only loaded on first API request. This enables fast container startup and allows Docker healthchecks to pass before model download completes.

**Hardware Detection**: The OCREngine class (app/ocr_engine.py:44-63) detects CUDA availability at initialization time and stores it in `self.device`. This decision is made once and reused for all subsequent requests.

**BGR/RGB Conversions**: The API pipeline converts images multiple times:
1. PIL Image (RGB) loaded from upload (app/main.py:88)
2. Converted to BGR ndarray for consistency (app/main.py:96)
3. Converted back to RGB for EasyOCR (app/ocr_engine.py:112)
This ensures compatibility with both OpenCV and EasyOCR expectations.

**Bounding Box Format**: All bounding boxes use 4-corner format `[[x0,y0], [x1,y1], [x2,y2], [x3,y3]]` (clockwise from top-left), not x/y/w/h rectangles. This preserves rotation information.

## Configuration & Customization

### Language Configuration
Edit `app/ocr_engine.py:32` to change languages:
```python
languages = ['en', 'fr', 'de', 'es', 'it', 'pt']  # Default
# Or customize: ['en', 'de'] or ['en', 'zh-cn', 'ja']
```
See [EasyOCR supported languages](https://github.com/JaidedAI/EasyOCR#supported-languages) for all codes.

### Environment Variables
- `LOG_LEVEL`: DEBUG, INFO (default), WARNING, ERROR
- `PORT`: Port for local development (default: 3600)

### Model Preloading
The Dockerfile (lines 33-40) preloads EasyOCR models at build time (~140MB download). This ensures the first API request is fast. If you modify language configuration, the Docker build will download different models.

## Performance Considerations

**Hardware Performance**:
- CPU (M4): 11-12s per image
- GPU (RTX 3060): ~2.5s per image (4-5x faster)
- GPU (RTX 4090): ~1.7s per image (6-7x faster)

**Memory Requirements**:
- CPU: 2GB+ RAM
- GPU: 2GB+ VRAM (typically uses 1-2GB)

**GPU Detection**: Check logs on startup for "CUDA GPU detected: [model name]" or "Using CPU for inference". The device is also returned by the `/_health` endpoint.

## Important Implementation Details

**Request Processing Flow** (app/main.py:56-136):
1. Load and validate image upload
2. Convert PIL → BGR ndarray
3. Run OCR (timed separately)
4. Convert results to JSON-friendly structure
5. Generate searchable PDF
6. Return both JSON and base64 PDF

**Error Handling**: All exceptions during OCR processing (app/main.py:105-107) are caught and returned as HTTP 500 with error details. Check logs for full stack traces.

**Logging**: Structured logging with timing information for:
- File upload (size, dimensions)
- Image loading time
- OCR processing time
- PDF generation time
- Total request time

**Confidence Scores**: OCR results include per-text confidence (0.0-1.0). Typical values for clean text are 0.95-0.99. Lower scores may indicate poor image quality or handwritten text.

## Common Development Tasks

### Adding New Endpoints
Add route handlers in `app/main.py`. Follow existing patterns:
- Use type hints and Pydantic models for request/response
- Add structured logging
- Include timing measurements for performance tracking
- Tag endpoints appropriately for API docs

### Modifying OCR Behavior
Key parameters in `app/ocr_engine.py` EasyOCR reader initialization (lines 82-87):
- `gpu`: Automatically set based on hardware detection
- `quantize`: Set to `True` for faster but slightly less accurate inference
- `verbose`: Currently `False` to reduce log noise

The `readtext()` call (lines 116-120) uses:
- `detail=1`: Return bounding boxes
- `paragraph=False`: Don't merge detected lines

### Working with Bounding Boxes
Bounding boxes in responses use coordinates from top-left origin (standard image coordinates). The PDF generation (app/make_pdf.py:30-34) converts to PDF coordinate system (bottom-left origin) via: `y_pdf = img_height - y0 - text_height`.

## Deployment Notes

The Docker image preloads models at build time, making it production-ready. The healthcheck (Dockerfile:45-46) verifies the API is responding before marking the container as healthy.

For GPU deployment, ensure:
- nvidia-docker runtime is installed
- Container runs with `--gpus all` flag or equivalent configuration
- CUDA 11.0+ compatible GPU

The application automatically detects and uses GPU when available - no code changes needed between CPU and GPU deployments.
