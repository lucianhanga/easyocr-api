# Docker Image Setup Guide

This project provides two optimized Docker images for OCR processing:

## 1. GPU-Optimized Image (Dockerfile.gpu)
**Best for: NVIDIA GPU systems**

### Features:
- Uses NVIDIA CUDA 12.1.0 runtime
- Parallel processing of 4 PDF pages simultaneously
- GPU-accelerated OCR with EasyOCR
- Optimized dependencies for GPU inference

### Requirements:
- NVIDIA GPU with CUDA support
- nvidia-docker2 installed
- Docker Compose

### Build and Run:
```bash
# Build
docker-compose -f docker-compose.gpu.yml build

# Run
docker-compose -f docker-compose.gpu.yml up -d

# View logs
docker-compose -f docker-compose.gpu.yml logs -f
```

### Environment Variables:
- `GPU_MEMORY_LIMIT`: GPU memory limit (default: 0 = unlimited)
- `MAX_WORKERS`: Parallel page processing workers (default: 4)
- `LOG_LEVEL`: Logging level (default: INFO)

## 2. CPU-Optimized Image (Dockerfile.cpu)
**Best for: Multi-core CPU systems without GPU**

### Features:
- Uses Python 3.11 slim base image
- Parallel processing of 8 PDF pages simultaneously
- Optimized for multi-core CPUs
- Lighter dependencies (no CUDA)

### Build and Run:
```bash
# Build
docker-compose -f docker-compose.cpu.yml build

# Run
docker-compose -f docker-compose.cpu.yml up -d

# View logs
docker-compose -f docker-compose.cpu.yml logs -f
```

### Environment Variables:
- `MAX_WORKERS`: Parallel page processing workers (default: 8 for CPU)
- `LOG_LEVEL`: Logging level (default: INFO)
- `OMP_NUM_THREADS`: OpenMP threads for CPU parallelization

## Key Differences

| Feature | GPU Version | CPU Version |
|---------|-------------|-------------|
| Base Image | NVIDIA CUDA 12.1.0 | Python 3.11 Slim |
| Default Workers | 4 | 8 |
| OCR Backend | GPU-accelerated | CPU multi-threaded |
| Image Size | ~6-7 GB | ~2-3 GB |
| Dependencies | PyTorch with CUDA | PyTorch CPU-only |
| Best Use Case | High-volume, fast processing | Cost-effective, no GPU needed |

## Quick Start

### For GPU systems:
```bash
./run.sh gpu
```

### For CPU systems:
```bash
./run.sh cpu
```

## Testing

Test with the included client:
```bash
# Install client dependencies
pip install requests

# Run OCR on a PDF
./examples/ocr_client.py /path/to/your/document.pdf

# Run OCR on an image
./examples/ocr_client.py /path/to/your/image.png
```

## Performance Tips

### GPU Version:
- Increase `MAX_WORKERS` if you have multiple GPUs
- Monitor GPU usage with `nvidia-smi` or `nvtop`
- Set `GPU_MEMORY_LIMIT` if running other GPU workloads

### CPU Version:
- Set `MAX_WORKERS` to match your CPU core count
- Increase `OMP_NUM_THREADS` for better parallelization
- Use on systems with 8+ CPU cores for best performance

## Troubleshooting

### GPU version not using GPU:
```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Verify nvidia-docker2 is installed
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Out of memory errors:
- Reduce `MAX_WORKERS`
- Set `GPU_MEMORY_LIMIT` (GPU version)
- Process smaller batches of pages

### Build fails with timezone prompt:
- The Dockerfiles now include non-interactive timezone configuration
- Default timezone: Europe/London
- Modify `TZ` variable in Dockerfile if needed
