#!/usr/bin/env bash
# entrypoint.sh – Start Xvfb virtual display then launch the Telegram bot
set -e

DISPLAY_NUM="${DISPLAY_NUM:-1}"
DISPLAY_W="${DISPLAY_WIDTH:-1280}"
DISPLAY_H="${DISPLAY_HEIGHT:-800}"

echo "[+] Starting Xvfb virtual display :${DISPLAY_NUM} (${DISPLAY_W}x${DISPLAY_H}x24)…"
Xvfb ":${DISPLAY_NUM}" -screen 0 "${DISPLAY_W}x${DISPLAY_H}x24" &
XVFB_PID=$!

export DISPLAY=":${DISPLAY_NUM}"

# Give Xvfb a moment to start
sleep 1

# Start a lightweight window manager so windows render properly
if command -v xfwm4 >/dev/null 2>&1; then
    xfwm4 --daemon 2>/dev/null || true
fi

echo "[+] Starting Bottel Kali bot…"
exec python3 bot.py
