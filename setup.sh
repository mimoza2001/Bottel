#!/usr/bin/env bash
# setup.sh – Bootstrap the Bottel Kali Linux cybersecurity bot
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[+]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[-]${NC} $*"; exit 1; }

# ── Checks ─────────────────────────────────────────────────────────────────────
command -v docker  >/dev/null 2>&1 || error "Docker is not installed. Install it first."
command -v docker compose >/dev/null 2>&1 \
    || docker-compose --version >/dev/null 2>&1 \
    || error "Docker Compose is not installed."

# ── .env ───────────────────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
    warn ".env not found – copying from .env.example"
    cp .env.example .env
    warn "Edit .env and set TELEGRAM_BOT_TOKEN before running the bot."
fi

# Verify token is set
# shellcheck source=/dev/null
source .env
if [[ "${TELEGRAM_BOT_TOKEN:-your_telegram_bot_token_here}" == "your_telegram_bot_token_here" ]]; then
    warn "TELEGRAM_BOT_TOKEN is not set in .env. Edit .env before starting."
fi

# ── Directories ─────────────────────────────────────────────────────────────────
info "Creating results/ and wordlists/ directories…"
mkdir -p results wordlists

# ── Build ───────────────────────────────────────────────────────────────────────
info "Building Kali Docker image (this may take several minutes on first run)…"
docker compose build

info "Setup complete!"
echo ""
echo "  To start the bot:"
echo "    docker compose up -d"
echo ""
echo "  To open an interactive Kali shell:"
echo "    docker compose --profile shell run kali-shell bash"
echo ""
echo "  To view bot logs:"
echo "    docker compose logs -f kali-bot"
echo ""
warn "REMINDER: Only scan/test systems you own or have explicit written permission to test."
