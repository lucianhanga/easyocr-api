#!/bin/bash
# Verify ROCm setup and GPU detection
# Run this after reboot to confirm everything is working

echo "======================================"
echo "ROCm GPU Verification"
echo "======================================"
echo ""

# Check ROCm installation
echo "1. Checking ROCm installation..."
if command -v rocm-smi &> /dev/null; then
    echo "✅ rocm-smi found"
    ROCM_VERSION=$(dpkg -l | grep rocm-core | awk '{print $3}')
    echo "   ROCm version: $ROCM_VERSION"
else
    echo "❌ rocm-smi not found - ROCm not installed or not in PATH"
    exit 1
fi

echo ""
echo "2. Checking GPU detection..."
if rocm-smi &> /dev/null; then
    echo "✅ GPU detected:"
    rocm-smi | grep -A 1 "GPU"
else
    echo "❌ No GPU detected by ROCm"
    echo "   Make sure you're on an AMD GPU VM (NV8as v4)"
    exit 1
fi

echo ""
echo "3. Checking user permissions..."
if groups | grep -q "video"; then
    echo "✅ User in 'video' group"
else
    echo "❌ User NOT in 'video' group"
    echo "   Run: sudo usermod -a -G video $USER"
    echo "   Then logout/login or reboot"
fi

if groups | grep -q "render"; then
    echo "✅ User in 'render' group"
else
    echo "❌ User NOT in 'render' group"
    echo "   Run: sudo usermod -a -G render $USER"
    echo "   Then logout/login or reboot"
fi

echo ""
echo "4. Checking ROCm devices..."
if [ -c /dev/kfd ]; then
    echo "✅ /dev/kfd exists"
    ls -l /dev/kfd
else
    echo "❌ /dev/kfd not found"
fi

if [ -d /dev/dri ]; then
    echo "✅ /dev/dri exists"
    ls -l /dev/dri
else
    echo "❌ /dev/dri not found"
fi

echo ""
echo "5. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker installed"
    docker --version
    
    if groups | grep -q "docker"; then
        echo "✅ User in 'docker' group"
    else
        echo "⚠️  User NOT in 'docker' group (optional)"
    fi
else
    echo "❌ Docker not installed"
fi

echo ""
echo "6. Testing PyTorch with ROCm..."
if command -v python3 &> /dev/null; then
    echo "Testing PyTorch ROCm support..."
    docker run --rm \
        --device=/dev/kfd \
        --device=/dev/dri \
        --group-add video \
        --group-add render \
        rocm/pytorch:rocm6.1.3_ubuntu22.04_py3.10_pytorch_release-2.1.2 \
        python -c "import torch; print(f'✅ PyTorch ROCm available: {torch.cuda.is_available()}'); print(f'   Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU only\"}')" 2>/dev/null || echo "⚠️  Could not test PyTorch (Docker issue or first run)"
else
    echo "⚠️  Python3 not found"
fi

echo ""
echo "======================================"
echo "Verification Summary"
echo "======================================"
echo ""

# Check if all critical components are OK
if command -v rocm-smi &> /dev/null && \
   rocm-smi &> /dev/null && \
   groups | grep -q "video" && \
   groups | grep -q "render" && \
   [ -c /dev/kfd ] && \
   [ -d /dev/dri ] && \
   command -v docker &> /dev/null; then
    echo "✅ All checks passed!"
    echo ""
    echo "You're ready to build and run the ROCm container:"
    echo ""
    echo "    docker-compose -f docker-compose.rocm.yml build"
    echo "    docker-compose -f docker-compose.rocm.yml up -d"
    echo ""
    echo "Monitor with:"
    echo "    docker logs -f easyocr-api-rocm"
    echo "    watch -n 1 rocm-smi"
else
    echo "❌ Some checks failed - see messages above"
    echo ""
    echo "Common fixes:"
    echo "  - Reboot if you just installed ROCm"
    echo "  - Check you're on AMD GPU VM (Standard NV8as v4)"
    echo "  - Run setup script: ./setup-rocm.sh"
fi

echo ""
