#!/bin/bash

# activate_venv.sh - Quick virtual environment activation script

# Get the project root directory (parent of tools folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/venv"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo -e "${RED}Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Run ./tools/setup_venv.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}Activating virtual environment...${NC}"
echo -e "${YELLOW}To deactivate later, run: deactivate${NC}"
echo ""

# This script needs to be sourced to work properly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "${YELLOW}Note: This script should be sourced to work properly:${NC}"
    echo -e "${GREEN}source ./tools/activate_venv.sh${NC}"
    echo ""
    echo -e "${YELLOW}Or use the direct activation command:${NC}"
    echo -e "${GREEN}source $VENV_PATH/bin/activate${NC}"
else
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}Virtual environment activated!${NC}"
fi