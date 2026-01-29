#!/bin/bash
# learnlock installer script
# Usage: curl -fsSL https://raw.githubusercontent.com/MitudruDutta/learnlock/main/install.sh | bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗"
echo "██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝"
echo "██║     █████╗  ███████║██████╔╝██╔██╗ ██║██║     ██║   ██║██║     █████╔╝ "
echo "██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗ "
echo "███████╗███████╗██║  ██║██║  ██║██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗"
echo "╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo "Installing learnlock..."
echo

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    echo "Install Python 3.11+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION+ required, but found $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}OK:${NC} Python $PYTHON_VERSION detected"

# Install via pip
echo "Installing learnlock via pip..."
pip3 install --upgrade learnlock

# Verify installation
if command -v learnlock &> /dev/null; then
    echo
    echo -e "${GREEN}OK: learnlock installed successfully!${NC}"
    echo
    echo "Next steps:"
    echo "  1. Set your API key:"
    echo -e "     ${YELLOW}export GROQ_API_KEY=your_key${NC}"
    echo
    echo "  2. (Optional) Set Gemini key for better dialogue:"
    echo -e "     ${YELLOW}export GEMINI_API_KEY=your_key${NC}"
    echo
    echo "  3. Run learnlock:"
    echo -e "     ${YELLOW}learnlock${NC}"
    echo
else
    echo -e "${RED}Installation failed. Try: pip3 install learnlock${NC}"
    exit 1
fi
