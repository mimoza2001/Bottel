#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Python: pyproject.toml (Poetry or PEP 517)
if [ -f "pyproject.toml" ]; then
  if command -v poetry &>/dev/null; then
    echo "Installing Python dependencies via Poetry..."
    poetry install --no-interaction
  else
    echo "Installing Python dependencies via pip (pyproject.toml)..."
    pip install -e ".[dev]" --quiet 2>/dev/null || pip install -e "." --quiet
  fi

# Python: requirements files
elif [ -f "requirements-dev.txt" ]; then
  echo "Installing Python dev dependencies..."
  pip install -r requirements-dev.txt --quiet

elif [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies..."
  pip install -r requirements.txt --quiet

# Node.js
elif [ -f "package.json" ]; then
  echo "Installing Node.js dependencies..."
  npm install

# Go
elif [ -f "go.mod" ]; then
  echo "Downloading Go modules..."
  go mod download

# Rust
elif [ -f "Cargo.toml" ]; then
  echo "Building Rust dependencies..."
  cargo fetch

else
  echo "No dependency manifest found. Skipping dependency installation."
fi

echo "Session start hook completed."
