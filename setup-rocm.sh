#!/bin/bash
# Quick setup script for ROCm on Azure NV8as v4 VM
# For AMD Radeon Instinct MI25 GPU

set -e

echo "======================================"
echo "EasyOCR API - ROCm Setup for MI25"
echo "======================================"
echo ""

# Check if running on Ubuntu
if [ ! -f /etc/lsb-release ]; then
    echo "❌ This script is for Ubuntu only"
    exit 1
fi

# Check Ubuntu version
. /etc/lsb-release
if [ "$DISTRIB_RELEASE" != "22.04" ]; then
    echo "⚠️  Warning: This script is tested on Ubuntu 22.04"
    echo "   Your version: $DISTRIB_RELEASE"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Installing ROCm 6.1.3..."
echo "================================"

# Add ROCm repository
if [ ! -f /etc/apt/keyrings/rocm.gpg ]; then
    wget https://repo.radeon.com/rocm/rocm.gpg.key -O - | gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] https://repo.radeon.com/rocm/apt/6.1.3 jammy main" | sudo tee /etc/apt/sources.list.d/rocm.list
    sudo apt-get update
else
    echo "✅ ROCm repository already configured"
fi

# Install ROCm
if ! command -v rocm-smi &> /dev/null; then
    echo "Installing ROCm packages..."
    sudo apt-get install -y rocm-hip-sdk rocm-libs
else
    echo "✅ ROCm already installed"
fi

# Add user to video and render groups
echo ""
echo "Step 2: Configuring user permissions..."
echo "========================================"
sudo usermod -a -G video,render $USER
echo "✅ Added $USER to video and render groups"

echo ""
echo "Step 3: Installing Docker..."
echo "============================="

# Install Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    rm /tmp/get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install docker-compose
if ! command -v docker-compose &> /dev/null; then
    sudo apt-get install -y docker-compose
    echo "✅ docker-compose installed"
else
    echo "✅ docker-compose already installed"
fi

echo ""
echo "Step 4: Testing ROCm..."
echo "======================="

if command -v rocm-smi &> /dev/null; then
    echo "Running rocm-smi..."
    rocm-smi || echo "⚠️  ROCm installed but GPU not detected yet - reboot required"
else
    echo "⚠️  ROCm tools not in PATH yet - reboot required"
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "⚠️  IMPORTANT: You must REBOOT for changes to take effect:"
echo ""
echo "    sudo reboot"
echo ""
echo "After reboot, verify with:"
echo "    rocm-smi                    # Should show your MI25 GPU"
echo "    groups                      # Should include 'video' and 'render'"
echo ""
echo "Then build and run the container:"
echo "    cd $(pwd)"
echo "    docker-compose -f docker-compose.rocm.yml build"
echo "    docker-compose -f docker-compose.rocm.yml up -d"
echo ""
echo "Check logs:"
echo "    docker logs -f easyocr-api-rocm"
echo ""
echo "Test GPU detection:"
echo "    curl http://localhost:3600/_health"
echo ""
echo "See ROCM_SETUP.md for detailed instructions."
echo ""
