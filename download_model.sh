#!/usr/bin/env bash
# Downloads Qwen3.5-9B Q4_K_M GGUF model from Hugging Face
# Source: lmstudio-community/Qwen3.5-9B-GGUF (no login required)
# File size: ~5.6 GB

set -e

REPO="lmstudio-community/Qwen3.5-9B-GGUF"
FILE="Qwen3.5-9B-Q4_K_M.gguf"
URL="https://huggingface.co/${REPO}/resolve/main/${FILE}"
DEST_DIR="${HOME}/models/qwen3.5-9b"
DEST="${DEST_DIR}/${FILE}"

mkdir -p "$DEST_DIR"
echo "==> Saving to: $DEST"
echo "==> File size: ~5.6 GB  (this will take a while on slow connections)"
echo ""

# Resume-capable download with wget or curl
if command -v wget &>/dev/null; then
    wget -c --show-progress -O "$DEST" "$URL"
elif command -v curl &>/dev/null; then
    curl -L -C - --progress-bar -o "$DEST" "$URL"
else
    echo "ERROR: wget or curl is required. Install one and re-run."
    exit 1
fi

echo ""
echo "==> Done! Model saved to: $DEST"
echo "==> You can now load it with llama.cpp, LM Studio, Ollama, or any GGUF-compatible tool."
