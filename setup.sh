#!/usr/bin/env bash
# H1B Salary Database — One-command setup
# Run this once after cloning: bash setup.sh

set -e

echo ""
echo "=== H1B Salary Database Setup ==="
echo ""

# 1. Check Node.js
if ! command -v node &>/dev/null; then
  echo "ERROR: Node.js is required. Install it from https://nodejs.org (version 18+)"
  exit 1
fi

NODE_VER=$(node -e "process.exit(parseInt(process.version.slice(1)) < 18 ? 1 : 0)" 2>/dev/null && echo "ok" || echo "old")
if [ "$NODE_VER" = "old" ]; then
  echo "ERROR: Node.js 18+ required. Current: $(node --version)"
  exit 1
fi

echo "Node.js: $(node --version) ✓"

# 2. Check Python
if ! command -v python3 &>/dev/null; then
  echo "WARNING: Python 3 not found. Skipping database seed — run manually later."
  SKIP_SEED=1
else
  echo "Python:  $(python3 --version) ✓"
  SKIP_SEED=0
fi

# 3. Install npm dependencies
echo ""
echo "Installing dependencies..."
npm install --silent

# 4. Seed database (uses built-in sample data if no DOL files present)
if [ "$SKIP_SEED" = "0" ]; then
  echo ""
  echo "Seeding database with sample data..."
  python3 scripts/process_h1b_data.py --seed
fi

# 5. Copy env file if not present
if [ ! -f .env.local ]; then
  cp .env.example .env.local
  echo ""
  echo "Created .env.local — edit it with your domain before deploying."
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  npm run dev          → Start development server at http://localhost:3000"
echo "  npm run build        → Build production site"
echo "  vercel --prod        → Deploy to Vercel (requires: npm i -g vercel)"
echo ""
echo "To load real DOL data:"
echo "  1. Download H1B Excel files from https://www.dol.gov/agencies/eta/foreign-labor/performance"
echo "  2. Run: python3 scripts/process_h1b_data.py --input /path/to/downloads/"
echo ""
