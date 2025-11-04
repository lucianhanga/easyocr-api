# EasyOCR API - Deployment Guide

This project provides two optimized Docker images for different hardware configurations.

## 🚀 Quick Start

### GPU Deployment (NVIDIA CUDA)
**Optimized for:** NVIDIA GPUs with CUDA support  
**Best for:** High-volume production workloads, fastest inference

```bash
# Build and run GPU-optimized container
docker-compose -f docker-compose.gpu.yml up -d

# Or use the default docker-compose.yml (points to GPU)
docker-compose up -d
```

### CPU Deployment (Multi-core)
**Optimized for:** Multi-core CPUs without GPU  
**Best for:** Development, testing, or GPU-unavailable environments

```bash
# Build and run CPU-optimized container
docker-compose -f docker-compose.cpu.yml up -d
```

---

## 📦 Image Differences

### GPU Image (`Dockerfile.gpu`)
- **Base:** `nvidia/cuda:12.1.0-runtime-ubuntu22.04`
- **PyTorch:** Full CUDA support
- **Optimization:** Single worker, GPU memory management
- **Parallelization:** 4 pages processed in parallel (ThreadPoolExecutor)
- **Size:** ~5-6 GB
- **Performance:** 5-10x faster than CPU for OCR

### CPU Image (`Dockerfile.cpu`)
- **Base:** `python:3.11-slim`
- **PyTorch:** CPU-only (smaller footprint)
- **Optimization:** Multi-threaded CPU, 4+ cores recommended
- **Parallelization:** 4 pages processed in parallel (ThreadPoolExecutor)
- **Size:** ~2-3 GB
- **Performance:** Good for moderate workloads on multi-core systems

---

## 🔧 Configuration

### CPU Optimization (Environment Variables)
Adjust thread counts based on your CPU cores:

```yaml
environment:
  - OMP_NUM_THREADS=4
  - MKL_NUM_THREADS=4
  - OPENBLAS_NUM_THREADS=4
  - TORCH_NUM_THREADS=4
```

For 8-core CPU, use `8` instead of `4`.

### GPU Optimization
```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0  # Use first GPU
  - NVIDIA_VISIBLE_DEVICES=all
```

---

## 📊 Resource Allocation

### CPU Container
```yaml
deploy:
  resources:
    limits:
      cpus: '8'      # Max CPU cores
      memory: 8G     # Max memory
    reservations:
      cpus: '4'      # Reserved cores
      memory: 4G     # Reserved memory
```

### GPU Container
```yaml
deploy:
  resources:
    limits:
      memory: 8G     # Max memory
    reservations:
      devices:
        - driver: nvidia
          count: 1   # Number of GPUs
          capabilities: [gpu]
      memory: 4G
```

---

## 🏗️ Building Images

### Build GPU image
```bash
docker build -f Dockerfile.gpu -t easyocr-api:gpu .
```

### Build CPU image
```bash
docker build -f Dockerfile.cpu -t easyocr-api:cpu .
```

---

## 🧪 Testing

```bash
# Install test client dependencies
pip install requests

# Test the API
./examples/ocr_client.py path/to/your.pdf

# Or use curl
curl -X POST http://localhost:3600/ocr \
  -F "file=@/path/to/your.pdf" \
  -o output.json
```

---

## 📈 Performance Comparison

| Metric | CPU (8 cores) | GPU (Tesla T4) |
|--------|---------------|----------------|
| Single page | ~3-5s | ~0.5-1s |
| 10 pages (parallel) | ~8-12s | ~2-3s |
| 100 pages | ~80-120s | ~20-30s |
| Memory usage | 4-6 GB | 6-8 GB |

*Results vary based on image size and complexity*

---

## 🛠️ Switching Between CPU and GPU

### Stop current container
```bash
docker-compose down
```

### Start GPU version
```bash
docker-compose -f docker-compose.gpu.yml up -d
```

### Start CPU version
```bash
docker-compose -f docker-compose.cpu.yml up -d
```

---

## 📝 Dependencies

### Common (Both Images)
- FastAPI + Uvicorn
- EasyOCR
- PyMuPDF (PDF handling)
- OpenCV (image processing)
- Pillow (image manipulation)

### GPU-Specific
- PyTorch with CUDA support
- NVIDIA CUDA Runtime 12.1

### CPU-Specific
- PyTorch CPU-only (from https://download.pytorch.org/whl/cpu)

---

## 🔍 Monitoring

### Check container status
```bash
docker-compose ps
```

### View logs
```bash
# GPU
docker-compose -f docker-compose.gpu.yml logs -f

# CPU
docker-compose -f docker-compose.cpu.yml logs -f
```

### Health check
```bash
curl http://localhost:3600/_health
```

---

## 🐛 Troubleshooting

### GPU not detected
1. Verify nvidia-docker is installed: `docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi`
2. Check NVIDIA drivers: `nvidia-smi`
3. Ensure docker-compose version >= 1.28.0

### CPU performance issues
1. Increase CPU allocation in `docker-compose.cpu.yml`
2. Adjust thread environment variables
3. Monitor with: `docker stats easyocr-api-cpu`

### Memory issues
1. Reduce page parallelization in `app/main.py` (change ThreadPoolExecutor `max_workers`)
2. Increase memory limits in docker-compose
3. Process smaller batches

---

## 📄 License

See LICENSE file for details.
