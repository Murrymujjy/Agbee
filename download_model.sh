#!/usr/bin/env bash
# Downloads the submission's GGUF weight file to model/.
# Must be idempotent, require no credentials, and land at the exact
# path referenced by metadata.json -> _runtime.model_path.
set -euo pipefail

# TODO: replace with your actual public model URL once the bake-off (Section 5.1
# of the proposal) picks a winner and it's quantised + uploaded to HF or a
# GitHub Release.
MODEL_URL="https://huggingface.co/TODO-your-org/TODO-your-model/resolve/main/TODO-your-model-Q4_K_M.gguf"
MODEL_PATH="model/your-model.gguf"   # must match metadata.json _runtime.model_path exactly

mkdir -p model

if [ -f "$MODEL_PATH" ]; then
    echo "Model already present at $MODEL_PATH — skipping download (idempotent)."
    exit 0
fi

echo "Downloading model to $MODEL_PATH ..."
curl -L --fail -o "$MODEL_PATH" "$MODEL_URL"
echo "Done."
