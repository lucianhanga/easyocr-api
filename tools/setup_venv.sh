#!/bin/bash

# setup_venv.sh - Virtual Environment Setup Script for EasyOCR API
# This script creates a virtual environment with either full server deps or client-only deps

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory (parent of tools folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"
FULL_REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
CLIENT_REQUIREMENTS="$PROJECT_ROOT/requirements.client.txt"

echo -e "${BLUE}EasyOCR API - Virtual Environment Setup${NC}"
echo "========================================"
echo -e "Project root: ${YELLOW}$PROJECT_ROOT${NC}"
echo -e "Virtual env:  ${YELLOW}$VENV_PATH${NC}"
echo ""

# Ask user what type of setup they want
echo -e "${YELLOW}Choose setup type:${NC}"
echo "1) Full server setup (EasyOCR, PyTorch, CUDA support) - ~4GB download"
echo "2) Client-only setup (lightweight, no server deps) - ~50MB download"
echo ""
read -p "Enter choice (1 or 2): " -n 1 -r SETUP_CHOICE
echo ""

case $SETUP_CHOICE in
    1)
        SETUP_TYPE="full"
        REQUIREMENTS_FILE="$FULL_REQUIREMENTS"
        echo -e "${BLUE}Setting up FULL environment with server dependencies${NC}"
        ;;
    2)
        SETUP_TYPE="client"
        REQUIREMENTS_FILE="$CLIENT_REQUIREMENTS"
        echo -e "${BLUE}Setting up CLIENT-ONLY environment (lightweight)${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice. Please run the script again and choose 1 or 2.${NC}"
        exit 1
        ;;
esac
echo ""
echo -e "${YELLOW}Setup options:${NC}"
echo -e "  ${GREEN}Full setup${NC} - Installs server + client dependencies (EasyOCR, PyTorch, etc.)"
echo -e "  ${GREEN}Client only${NC} - Use ./tools/setup_client_venv.sh for lightweight client tools"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed or not in PATH${NC}"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "Found Python: ${GREEN}$PYTHON_VERSION${NC}"

# Check Python version (minimum 3.8)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}Error: Python 3.8+ is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}Error: Requirements file not found at $REQUIREMENTS_FILE${NC}"
    exit 1
fi

# Remove existing venv if it exists and user confirms
if [ -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Virtual environment already exists at $VENV_PATH${NC}"
    read -p "Do you want to remove it and create a fresh one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf "$VENV_PATH"
    else
        echo -e "${YELLOW}Using existing virtual environment${NC}"
        # Check if it's activated
        if [ -f "$VENV_PATH/bin/activate" ]; then
            echo ""
            echo -e "${GREEN}To activate the virtual environment, run:${NC}"
            echo -e "${BLUE}source $VENV_PATH/bin/activate${NC}"
            echo ""
            echo -e "${GREEN}To run the OCR client:${NC}"
            echo -e "${BLUE}cd $PROJECT_ROOT${NC}"
            echo -e "${BLUE}./tools/ocr_client.py /path/to/your/file.pdf${NC}"
            exit 0
        fi
    fi
fi

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv "$VENV_PATH"

if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo -e "${RED}Error: Failed to create virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}Virtual environment created successfully${NC}"

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install wheel for better package builds
pip install wheel

# Install requirements
echo -e "${BLUE}Installing $SETUP_TYPE requirements from $REQUIREMENTS_FILE...${NC}"
pip install -r "$REQUIREMENTS_FILE"

# Verify installation
echo ""
echo -e "${BLUE}Verifying installation...${NC}"
echo -e "${YELLOW}Installed packages:${NC}"

if [ "$SETUP_TYPE" = "full" ]; then
    pip list | grep -E "(fastapi|easyocr|torch|requests|PyMuPDF|Pillow|opencv|reportlab)" || echo "Some packages may not be visible in this view"
else
    pip list | grep -E "(requests|PyMuPDF|Pillow|reportlab)" || echo "Some packages may not be visible in this view"
fi

echo ""
echo -e "${GREEN}✅ Virtual environment setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Activate the virtual environment:"
echo -e "   ${BLUE}source $VENV_PATH/bin/activate${NC}"
echo ""

if [ "$SETUP_TYPE" = "full" ]; then
    echo -e "2. Start the EasyOCR API server:"
    echo -e "   ${BLUE}cd $PROJECT_ROOT${NC}"
    echo -e "   ${BLUE}uvicorn app.main:app --host 0.0.0.0 --port 3600${NC}"
    echo ""
    echo -e "3. Or test with the OCR client:"
    echo -e "   ${BLUE}./tools/ocr_client.py /path/to/your/file.pdf${NC}"
else
    echo -e "2. Use the OCR client (requires running server elsewhere):"
    echo -e "   ${BLUE}./tools/ocr_client.py /path/to/your/file.pdf${NC}"
    echo ""
    echo -e "${YELLOW}Note: Client-only setup cannot run the server.${NC}"
    echo -e "${YELLOW}For server functionality, re-run with option 1 or use Docker.${NC}"
fi

echo ""
echo -e "${YELLOW}For Docker deployment, see DOCKER_SETUP.md${NC}"
echo ""