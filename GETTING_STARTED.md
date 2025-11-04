# Getting Started with EasyOCR API

## Installation

### Prerequisites

- **Docker:** Version 20.10+ (recommended)
- **Python:** 3.11+ (for local development)
- **GPU (optional):** NVIDIA GPU with CUDA 11.0+ and nvidia-docker

### Option 1: Docker (Recommended)

1. **Build the image:**
   ```bash
   docker build -t easyocr-api .
   ```

2. **Run the container:**
   ```bash
   # CPU mode
   docker run -p 8000:8000 easyocr-api

   # GPU mode (requires nvidia-docker)
   docker run --gpus all -p 8000:8000 easyocr-api
   ```

3. **Test it:**
   ```bash
   curl http://localhost:8000/_health
   ```

### Option 2: Docker Compose

1. **Start the service:**
   ```bash
   docker-compose up
   ```

2. **For GPU:**
   ```bash
   docker-compose -f docker-compose.gpu.yml up
   ```

### Option 3: Local Development

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   Or use the helper script:
   ```bash
   ./run.sh
   ```

## First OCR Request

### Method 1: Python Client

```bash
# Generate a sample image
python examples/create_sample_image.py sample.png

# Run OCR on it
python examples/ocr_client.py sample.png
```

**Output:**
```
✅ Saved output.pdf (OCR items: 8)
```

### Method 2: cURL

```bash
curl -X POST http://localhost:8000/ocr \
  -F "file=@sample.png" \
  -o response.json

# Extract the PDF
cat response.json | jq -r '.pdf_base64' | base64 -d > output.pdf

# View OCR results
cat response.json | jq '.ocr_result'
```

### Method 3: Interactive API Docs

1. Open browser: http://localhost:8000/docs
2. Click "Try it out" on `/ocr` endpoint
3. Upload an image
4. Click "Execute"
5. View results

## Understanding the Response

### JSON Structure

```json
{
  "ocr_result": [
    {
      "text": "Hello World",
      "confidence": 0.98,
      "bbox": [[10, 20], [100, 20], [100, 40], [10, 40]]
    }
  ],
  "pdf_base64": "JVBERi0xLjQK..."
}
```

**Fields:**
- `text`: Extracted text string
- `confidence`: Recognition confidence (0.0-1.0, higher is better)
- `bbox`: Bounding box coordinates as 4 corner points `[top-left, top-right, bottom-right, bottom-left]`
- `pdf_base64`: Base64-encoded searchable PDF

### Decoding the PDF

**Python:**
```python
import base64
import json

with open('response.json') as f:
    data = json.load(f)

pdf_data = base64.b64decode(data['pdf_base64'])
with open('output.pdf', 'wb') as f:
    f.write(pdf_data)
```

**Bash:**
```bash
cat response.json | jq -r '.pdf_base64' | base64 -d > output.pdf
```

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Logging level
LOG_LEVEL=INFO

# Port (for local development)
PORT=8000
```

### Customizing Languages

Edit `app/ocr_engine.py` line 33 to change supported languages:

```python
# Default (European languages)
languages = ['en', 'fr', 'de', 'es', 'it', 'pt']

# Or customize:
languages = ['en', 'de']  # English + German only
languages = ['en', 'zh-cn', 'ja']  # English, Chinese, Japanese
```

See [EasyOCR documentation](https://github.com/JaidedAI/EasyOCR#supported-languages) for all language codes.

## Monitoring

### Health Check

```bash
curl http://localhost:8000/_health
```

**Response:**
```json
{
  "status": "ok",
  "model": "EasyOCR",
  "device": "cuda"  // or "cpu"
}
```

### Logs

**Docker:**
```bash
docker logs -f <container-id>
```

**Local:**
Logs printed to console with timestamps and severity levels.

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages

## Performance Tuning

### For CPU Deployment

1. **Reduce image size before processing:**
   - Resize to max 2000px width
   - Use JPEG with 85% quality

2. **Batch processing:**
   - Process multiple images concurrently
   - Use asyncio for parallel requests

### For GPU Deployment

1. **Batch size optimization:**
   - EasyOCR automatically batches text recognition
   - Larger batches on GPU = better utilization

2. **Monitor GPU memory:**
   - Use `nvidia-smi` to check VRAM usage
   - Typical usage: 1-2GB VRAM

## Troubleshooting

### "Model not found" error

The first run downloads ~140MB of models. This is normal and only happens once.

**Solution:** Wait for download to complete (1-3 minutes on first run).

### "Out of memory" error

**CPU:** Need 2GB+ RAM
**GPU:** Need 2GB+ VRAM

**Solution:** Reduce image size or use a machine with more memory.

### Slow performance on CPU

This is expected. CPU inference is 6-10x slower than GPU.

**Solutions:**
- Deploy to GPU instance
- Use smaller images
- Consider Tesseract for simple printed text (faster on CPU)

### GPU not being used

Check:
1. `docker run --gpus all` flag is present
2. nvidia-docker is installed: `docker run --gpus all nvidia/cuda:11.0-base nvidia-smi`
3. Container logs show "CUDA GPU detected"

## Next Steps

1. ✅ Test the API with your images
2. ✅ Review the accuracy and performance
3. ✅ Deploy to your preferred platform
4. ✅ Integrate with your application
5. ✅ Star the repo if you find it useful!

## Support

- **Documentation:** See README.md
- **Issues:** Open a GitHub issue
- **Questions:** Check existing issues or open a new one

Happy OCR-ing! 🎉
