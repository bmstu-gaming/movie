#!/bin/bash
export LANG=en_US.UTF-8


if [ ! -d ".venv" ]; then
    echo ".venv not found. creating..."
    python3 -m venv .venv
fi

VENV_PYTHON="$(pwd)/.venv/bin/python"

echo
echo "Checking virtual environment Python..."
if [ ! -f "$VENV_PYTHON" ]; then
    echo
    echo "Virtual environment Python not found at: $VENV_PYTHON"
    exit 1
fi

echo
echo "Python from environment:"
"$VENV_PYTHON" --version

echo
echo "Install dependencies from file requirements.txt..."
"$VENV_PYTHON" -m pip install -r requirements.txt > /dev/null 2>&1

echo
echo "Launching..."
"$VENV_PYTHON" main.py

read -p "Press Enter to continue..."
