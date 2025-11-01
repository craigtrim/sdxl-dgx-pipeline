#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-sdxl:local}"
HOST_DIR="${HOST_DIR:-/home/craigtrim/projects/sdxl}"           # project root
CONTAINER_DATA="/workspace/data"                                # inside container

# python prompt-generator on host
PY_GEN="${PY_GEN:-/home/craigtrim/projects/sdxl/sdxl_prompt_builder.py}"

# output targets
OUT_PROMPTS_DIR="${HOST_DIR}/resources/output/prompts"
OUT_PNG_DIR="${HOST_DIR}/resources/output/png"

# user idea → default if none
IDEA="${1:-portrait photo, high detail}"

info()    { echo -e "🔹 \033[1;34m$1\033[0m"; }
success() { echo -e "✅ \033[1;32m$1\033[0m"; }
error()   { echo -e "❌ \033[1;31m$1\033[0m"; }
warn()    { echo -e "⚠️  \033[1;33m$1\033[0m"; }

# -----------------------------------------------------------------------------
# prep host dirs
# -----------------------------------------------------------------------------
mkdir -p "$HOST_DIR" "$HOST_DIR/prompts"
mkdir -p "$OUT_PROMPTS_DIR" "$OUT_PNG_DIR"

# -----------------------------------------------------------------------------
# 1) build image
# -----------------------------------------------------------------------------
info "🏗️ building image: $IMAGE_NAME"
sudo docker build -t "$IMAGE_NAME" .

# -----------------------------------------------------------------------------
# 2) generate SDXL prompt on host via Ollama-backed python
# -----------------------------------------------------------------------------
TMP_PROMPT="$HOST_DIR/prompts/tmp.txt"
python "$PY_GEN" --idea "$IDEA" --out "$TMP_PROMPT"

PROMPT_CONTENT="$(cat "$TMP_PROMPT")"
MD5_HASH="$(printf '%s' "$PROMPT_CONTENT" | md5sum | awk '{print $1}')"

FINAL_PROMPT="$HOST_DIR/prompts/${MD5_HASH}.txt"
mv "$TMP_PROMPT" "$FINAL_PROMPT"

success "prompt → $FINAL_PROMPT"
info    "md5    → $MD5_HASH"

# -----------------------------------------------------------------------------
# 3) run container (named) so we can docker cp after
# -----------------------------------------------------------------------------
LOCAL_IMG_PATH="$HOST_DIR/${MD5_HASH}.png"
RUN_NAME="sdxl-run-${MD5_HASH}"

info "🎬 running container with GB10 flags"
sudo docker run -it --gpus all \
  --ipc=host \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --name "$RUN_NAME" \
  -v "$HOST_DIR":"$CONTAINER_DATA" \
  "$IMAGE_NAME" \
  /workspace/generate-image.sh \
    --prompt-file "$CONTAINER_DATA/prompts/${MD5_HASH}.txt" \
    --output "$CONTAINER_DATA/${MD5_HASH}.png"

# -----------------------------------------------------------------------------
# 4) copy out explicitly (even though we mounted)
# -----------------------------------------------------------------------------
info "📁 copying image from container → host"
sudo docker cp "$RUN_NAME":"$CONTAINER_DATA/${MD5_HASH}.png" "$LOCAL_IMG_PATH" || warn "copy skipped (likely already present via mount)"

# cleanup container
sudo docker rm "$RUN_NAME" >/dev/null 2>&1 || true

# -----------------------------------------------------------------------------
# 5) place into repo-friendly locations
# -----------------------------------------------------------------------------
FINAL_PROMPT_DEST="${OUT_PROMPTS_DIR}/${MD5_HASH}.txt"
FINAL_PNG_DEST="${OUT_PNG_DIR}/${MD5_HASH}.png"

cp "$FINAL_PROMPT" "$FINAL_PROMPT_DEST"
cp "$LOCAL_IMG_PATH" "$FINAL_PNG_DEST"

success "prompt → $FINAL_PROMPT_DEST"
success "image  → $FINAL_PNG_DEST"
