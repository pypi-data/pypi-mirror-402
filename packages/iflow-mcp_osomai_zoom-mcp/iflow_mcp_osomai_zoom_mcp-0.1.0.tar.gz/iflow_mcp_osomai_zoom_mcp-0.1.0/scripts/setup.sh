#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Zoom MCP Server...${NC}\n"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
    echo "Error: Python 3.11 or higher is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "\n${BLUE}Setting up Zoom API credentials...${NC}"
    python scripts/setup_zoom_auth.py
fi

# Test Zoom API connection
echo -e "\n${BLUE}Testing Zoom API connection...${NC}"
python scripts/test_zoom_connection.py

echo -e "\n${GREEN}Setup complete! You can now use the Zoom MCP server.${NC}"
echo -e "To start the server, run: ${BLUE}python -m zoom_mcp.server${NC}" 