#!/bin/bash

echo "============================================================"
echo "  GOOGLE ACCOUNT CHECKER - IMPROVED VERSION"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    echo "Please install Python 3.7+ and try again."
    exit 1
fi

echo "[INFO] Starting checker..."
echo ""

python3 checker.py

echo ""
echo "============================================================"
echo "  COMPLETED! Check results folder for output."
echo "============================================================"
