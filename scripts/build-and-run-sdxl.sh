#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_NAME="${IMAGE_NAME:-sdxl:local}"
HOST_DIR="${HOST_DIR:-${PROJECT_ROOT}}"

# canonical dirs
PROMPTS_DIR="${HOST_DIR}/resources/prompts"
OUT_PNG_DIR="${HOST_DIR}/resources/output/png"

PY_GEN_MODULE="sdxl_runner.prompt_builder"

CONTAINER_ROOT="/workspace/project"
CONTAINER_PROMPTS="${CONTAINER_ROOT}/resources/prompts"
CONTAINER_OUT_PNG="${CONTAINER_ROOT}/resources/output/png"

IDEA="${1:-portrait photo, high detail}"

info()    { echo -e "🔹 \033[1;34m$1\033[0m"; }
success() { echo -e "✅ \033[1;32m$1\033[0m"; }
error()   { echo -e "❌ \033[1;31m$1\033[0m"; }
warn()    { echo -e "⚠️  \033[1;33m$1\033[0m"; }

# ensure dirs
mkdir -p "${HOST_DIR}"
mkdir -p "${PROMPTS_DIR}"
mkdir -p "${OUT_PNG_DIR}"

# 1) build image
info "🏗️ building image: ${IMAGE_NAME}"
sudo docker build \
  -t "${IMAGE_NAME}" \
  -f "${PROJECT_ROOT}/docker/Dockerfile" \
  "${PROJECT_ROOT}"

# 2) generate prompt on host
TMP_PROMPT="${PROMPTS_DIR}/tmp.txt"

PYTHONPATH="${PROJECT_ROOT}/src" python -m "${PY_GEN_MODULE}" \
  --idea "${IDEA}" \
  --out "${TMP_PROMPT}"

PROMPT_CONTENT="$(cat "${TMP_PROMPT}")"
MD5_HASH="$(printf '%s' "${PROMPT_CONTENT}" | md5sum | awk '{print $1}')"

FINAL_PROMPT="${PROMPTS_DIR}/${MD5_HASH}.txt"
mv "${TMP_PROMPT}" "${FINAL_PROMPT}"

success "prompt → ${FINAL_PROMPT}"
info    "md5    → ${MD5_HASH}"

# 3) run container and write image directly to resources/output/png
RUN_NAME="sdxl-run-${MD5_HASH}"

info "🎬 running container with GPU flags"
sudo docker run -it --gpus all \
  --ipc=host \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --name "${RUN_NAME}" \
  -v "${HOST_DIR}:${CONTAINER_ROOT}" \
  "${IMAGE_NAME}" \
  /workspace/scripts/generate-image.sh \
    --prompt-file "${CONTAINER_PROMPTS}/${MD5_HASH}.txt" \
    --output "${CONTAINER_OUT_PNG}/${MD5_HASH}.png"

sudo docker rm "${RUN_NAME}" >/dev/null 2>&1 || true

success "image  → ${OUT_PNG_DIR}/${MD5_HASH}.png"
