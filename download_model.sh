#!/usr/bin/env bash
# Downloads Qwen3.5-9B Q4_K_M GGUF model from Hugging Face
#
# Usage:
#   ./download_model.sh
#   HF_TOKEN=hf_xxx ./download_model.sh   # with HuggingFace auth token
#
# The model will be saved to ~/models/qwen3.5-9b/

set -e

MODEL_REPO="Qwen/Qwen3.5-9B-GGUF"
MODEL_FILE="qwen3.5-9b-q4_k_m.gguf"

# bartowski typically mirrors GGUF quantizations for Qwen models
ALT_REPO="bartowski/Qwen3.5-9B-GGUF"
ALT_FILE="Qwen3.5-9B-Q4_K_M.gguf"

DEST_DIR="${HOME}/models/qwen3.5-9b"

mkdir -p "$DEST_DIR"
echo "==> Destination: $DEST_DIR"

# Optionally log in with a HuggingFace token
if [[ -n "$HF_TOKEN" ]]; then
    echo "==> Logging in with provided HF_TOKEN"
    huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential 2>/dev/null || true
fi

# ── Ensure huggingface_hub is available ──────────────────────────────────────
if ! python3 -c "import huggingface_hub" &>/dev/null; then
    echo "==> Installing huggingface_hub ..."
    pip3 install --quiet huggingface_hub
fi

# ── Install huggingface-cli if missing ───────────────────────────────────────
if ! command -v huggingface-cli &>/dev/null; then
    pip3 install --quiet "huggingface_hub[cli]"
fi

# ── Download ─────────────────────────────────────────────────────────────────
python3 - <<PYEOF
import os, sys
from huggingface_hub import hf_hub_download, HfApi

token = os.environ.get("HF_TOKEN") or None

candidates = [
    ("$MODEL_REPO", "$MODEL_FILE"),
    ("$ALT_REPO",   "$ALT_FILE"),
]

dest = "$DEST_DIR"
os.makedirs(dest, exist_ok=True)

success = False
for repo, fname in candidates:
    try:
        print(f"  Trying {repo}/{fname} ...")
        path = hf_hub_download(
            repo_id=repo,
            filename=fname,
            local_dir=dest,
            token=token,
        )
        print(f"\n  Model saved to: {path}")
        success = True
        break
    except Exception as e:
        print(f"  Failed ({type(e).__name__}): {e}")

if not success:
    print("""
ERROR: Could not download the model.

Possible reasons:
  1. The model repo does not exist yet on HuggingFace.
  2. You need a HuggingFace account/token.
     Create one at https://huggingface.co/join, then run:
       HF_TOKEN=hf_YOUR_TOKEN ./download_model.sh

  3. No internet access in this environment.

Once Qwen3.5-9B GGUF is publicly available, re-run this script.
""", file=sys.stderr)
    sys.exit(1)
PYEOF

echo "==> Download complete."
echo "    File location: $DEST_DIR"
