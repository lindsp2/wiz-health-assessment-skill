#!/usr/bin/env bash
set -e

echo "======================================================="
echo "     WIZ HEALTH ASSESSMENT & SKILLS INSTALLER          "
echo "======================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is required but not installed."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Install Python requirements if pip is available
if command -v pip3 &> /dev/null; then
    echo "[*] Checking Python dependencies..."
    pip3 install -r requirements.txt --quiet || true
elif command -v pip &> /dev/null; then
    echo "[*] Checking Python dependencies..."
    pip install -r requirements.txt --quiet || true
fi

# Run installer script
python3 scripts/install_skills.py
