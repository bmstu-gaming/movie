#!/bin/bash



if [ ! -d ".venv" ]; then
    echo ".venv not found. creating..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "venv activate check..."
if [ $? -ne 0 ]; then
    echo "failed to activate virtual environment. Exit."
    exit 1
fi
which python
pip --version

echo "install dependencies from file requirements.txt..."
pip install -r requirements.txt

echo "launch..."
python main.py
