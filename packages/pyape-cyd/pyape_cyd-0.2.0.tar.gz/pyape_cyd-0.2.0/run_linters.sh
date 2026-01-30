#!/usr/bin/env bash

# Stop script on first error
set -e

cd "$(dirname "$0")"

# Activate our venv
python3 -m venv venv
source venv/bin/activate

# Install linters
pip install mypy==1.13.0 pyright==1.1.387 ruff==0.7.2 --quiet

# Install lib deps
pip install -r requirements.txt --quiet

# Run mypy
echo ""
echo "Running Mypy..."
mypy --install-types --non-interactive --show-traceback --namespace-packages -p pyape

# Run pyright
echo ""
echo "Running Pyright..."
pyright pyape

# Run ruff
echo ""
echo "Running Ruff (and use --fix option)..."
cd pyape
ruff check --fix