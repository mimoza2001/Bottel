#!/usr/bin/env bash
# Download Qwen3.5-9B Q4_K_M GGUF model
# Usage: bash download_model.sh

set -e

MODEL_REPO="unsloth/Qwen3.5-9B-GGUF"
MODEL_FILE="Qwen3.5-9B-Q4_K_M.gguf"
MODELS_DIR="./models"

echo "=== Qwen3.5-9B Q4_K_M Model Downloader ==="

mkdir -p "$MODELS_DIR"

# Check for huggingface-hub CLI
if command -v huggingface-cli &>/dev/null; then
    echo "Using huggingface-cli..."
    huggingface-cli download "$MODEL_REPO" "$MODEL_FILE" \
        --local-dir "$MODELS_DIR" \
        --local-dir-use-symlinks False
    echo "Model saved to: $MODELS_DIR/$MODEL_FILE"

# Fallback: Python huggingface_hub
elif python3 -c "import huggingface_hub" 2>/dev/null; then
    echo "Using huggingface_hub Python library..."
    python3 - <<EOF
from huggingface_hub import hf_hub_download
path = hf_hub_download(
    repo_id="$MODEL_REPO",
    filename="$MODEL_FILE",
    local_dir="$MODELS_DIR",
    local_dir_use_symlinks=False,
)
print(f"Model saved to: {path}")
EOF

# Fallback: ollama
elif command -v ollama &>/dev/null; then
    echo "Using ollama..."
    ollama pull qwen3.5:9b-q4_K_M
    echo "Model pulled via ollama."

else
    echo "ERROR: No download method found."
    echo "Install one of the following:"
    echo "  pip install huggingface-hub"
    echo "  https://ollama.com"
    exit 1
fi

echo "Done!"
