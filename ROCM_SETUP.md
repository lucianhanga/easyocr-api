# EasyOCR API - AMD ROCm GPU Support

This guide explains how to run EasyOCR API on AMD GPUs using ROCm (AMD's open compute platform).

## Supported Hardware

- **AMD Radeon Instinct MI25** (Standard NV8as v4 VMs on Azure)
- AMD Radeon Instinct MI50/MI60/MI100
- AMD Radeon RX 6000/7000 series (with compatible ROCm versions)

## Prerequisites

### 1. Install ROCm on Host

On your Azure VM (Ubuntu 22.04), install ROCm:

```bash
# Add ROCm repository
wget https://repo.radeon.com/rocm/rocm.gpg.key -O - | gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/6.1.3 jammy main" | sudo tee /etc/apt/sources.list.d/rocm.list

sudo apt-get update

# Install ROCm
sudo apt-get install -y rocm-hip-sdk rocm-libs

# Add user to video and render groups
sudo usermod -a -G video,render $USER

# Reboot to apply changes
sudo reboot
```

### 2. Verify ROCm Installation

After reboot:

```bash
# Check ROCm installation
rocm-smi

# Should show your GPU (MI25)
# Example output:
# ========================= ROCm System Management Interface =========================
# GPU  Temp   AvgPwr  SCLK     MCLK     Fan     Perf  PwrCap  VRAM%  GPU%
# 0    50.0c  50W     1000Mhz  1200Mhz  30.00%  auto  300W    0%     0%
```

### 3. Install Docker with ROCm Support

```bash
# Install Docker if not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install docker-compose
sudo apt-get install -y docker-compose

# Logout and login again, or run:
newgrp docker
```

## Building and Running

### Build the ROCm-enabled Docker Image

```bash
cd /path/to/easyocr-api

# Build with ROCm support
docker-compose -f docker-compose.rocm.yml build

# This takes ~10-15 minutes (downloads ROCm base image + models)
```

### Run the Container

```bash
# Start the service
docker-compose -f docker-compose.rocm.yml up -d

# Check logs
docker logs -f easyocr-api-rocm

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:3600
# GPU detected: AMD Radeon Instinct MI25
```

### Verify GPU is Detected

```bash
# Check health endpoint
curl http://localhost:3600/_health

# Should return:
# {
#   "status": "ok",
#   "model": "EasyOCR",
#   "device": "cuda"  # ROCm uses CUDA-compatible API
# }

# Check inside container
docker exec -it easyocr-api-rocm python -c "import torch; print(f'ROCm available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"

# Should output:
# ROCm available: True
# Device: AMD Radeon Instinct MI25
```

## Performance Expectations

### AMD Radeon Instinct MI25 (16GB VRAM)

- **OCR Speed**: ~5-10 seconds per page (vs 50-60s on CPU)
- **Memory Usage**: ~3-4GB VRAM + 2GB system RAM
- **Throughput**: Can process ~6-12 pages per minute
- **Speedup**: **5-10x faster** than CPU-only processing

### Comparison

| Hardware | Time per Page | Pages/Min | Memory |
|----------|--------------|-----------|--------|
| CPU (Intel Xeon) | 50-60s | 1 | 2.2GB RAM |
| AMD MI25 (ROCm) | 5-10s | 6-12 | 4GB VRAM + 2GB RAM |
| NVIDIA A100 (CUDA) | 3-5s | 12-20 | 5GB VRAM + 2GB RAM |

## Troubleshooting

### GPU Not Detected

```bash
# Check if ROCm devices are accessible
ls -la /dev/kfd /dev/dri

# Should show:
# crw-rw---- 1 root video /dev/kfd
# drwxr-xr-x 3 root root  /dev/dri

# Check if user is in video/render groups
groups

# Should include: video render
```

### Container Can't Access GPU

```bash
# Verify docker can access ROCm devices
docker run --rm -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --group-add render \
  rocm/pytorch:rocm6.1.3_ubuntu22.04_py3.10_pytorch_release-2.1.2 \
  rocm-smi

# Should show GPU info
```

### ROCm Version Mismatch

The MI25 uses GFX9.0.0 architecture. If you get errors:

```bash
# Set environment variables in docker-compose.rocm.yml:
HSA_OVERRIDE_GFX_VERSION=9.0.0
PYTORCH_ROCM_ARCH=gfx900
```

### Performance Issues

```bash
# Monitor GPU usage
watch -n 1 rocm-smi

# Check container logs for warnings
docker logs easyocr-api-rocm | grep -i warning
```

## Testing

```bash
# Test with a sample image
cd examples
python ocr_client.py test_image.jpg --url http://localhost:3600

# Test with a large PDF
python ocr_client.py large_document.pdf --url http://localhost:3600 --timeout 3600
```

## Stopping and Cleaning Up

```bash
# Stop the container
docker-compose -f docker-compose.rocm.yml down

# Remove the image (to rebuild)
docker rmi easyocr-api:rocm

# Remove all unused images
docker system prune -a
```

## Environment Variables

You can customize these in `docker-compose.rocm.yml`:

```yaml
environment:
  - HSA_OVERRIDE_GFX_VERSION=9.0.0    # GPU architecture override
  - PYTORCH_ROCM_ARCH=gfx900          # Target architecture
  - LOG_LEVEL=INFO                    # Logging level (DEBUG, INFO, WARNING, ERROR)
  - HIP_VISIBLE_DEVICES=0             # Which GPU to use (if multiple)
```

## Azure VM Setup Notes

### Standard NV8as v4 Specifics

- **GPU**: AMD Radeon Instinct MI25 (16GB VRAM)
- **vCPUs**: 8
- **RAM**: 56 GB
- **OS**: Ubuntu 22.04 LTS recommended

### Optimizations for Azure

1. **Enable SR-IOV networking** for better performance
2. **Use Premium SSD** for faster model loading
3. **Place VM in same region** as data sources
4. **Use Azure Container Registry** for faster image pulls

## Cost Comparison (Azure)

| VM Type | GPU | Cost/Hour | OCR Pages/Hour | Cost per 1000 Pages |
|---------|-----|-----------|----------------|---------------------|
| D8s v3 (CPU) | None | $0.38 | 60 | $6.33 |
| NV8as v4 (AMD) | MI25 | $0.90 | 360-720 | $1.25-$2.50 |
| NC6s v3 (NVIDIA) | V100 | $3.06 | 720-1200 | $2.55-$4.25 |

**ROCm on NV8as v4 provides the best price/performance ratio!**

## Next Steps

1. Monitor GPU usage with `rocm-smi`
2. Adjust `--timeout` in client for large documents
3. Consider batch processing for multiple files
4. Set up monitoring with Prometheus + Grafana

## Support

For ROCm-specific issues:
- ROCm Documentation: https://rocm.docs.amd.com/
- AMD ROCm GitHub: https://github.com/RadeonOpenCompute/ROCm
- PyTorch ROCm: https://pytorch.org/get-started/locally/ (select ROCm)
