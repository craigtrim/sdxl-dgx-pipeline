#!/usr/bin/env bash
set -euo pipefail

# 🎯 wrapper to call the Python runner inside src/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHONPATH="${PROJECT_ROOT}/src"
PROMPTS_DIR="${PROJECT_ROOT}/prompts"
OUTPUT_DIR="${PROJECT_ROOT}/resources/output/png"

PROMPT_FILE="${PROMPTS_DIR}/prompt.txt"
OUTPUT_FILE="${OUTPUT_DIR}/out.png"
STEPS=30

info()    { echo -e "🔹 \033[1;34m$1\033[0m"; }
success() { echo -e "✅ \033[1;32m$1\033[0m"; }
error()   { echo -e "❌ \033[1;31m$1\033[0m"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt-file) PROMPT_FILE="$2"; shift 2 ;;
    --output)      OUTPUT_FILE="$2"; shift 2 ;;
    --steps)       STEPS="$2"; shift 2 ;;
    *)
      error "unknown arg: $1"
      exit 1
      ;;
  esac
done

if [[ ! -f "$PROMPT_FILE" ]]; then
  # allow relative to prompts/ if user passed just a name
  if [[ -f "${PROMPTS_DIR}/$PROMPT_FILE" ]]; then
    PROMPT_FILE="${PROMPTS_DIR}/$PROMPT_FILE"
  else
    error "prompt file not found: $PROMPT_FILE"
    exit 1
  fi
fi

mkdir -p "${OUTPUT_DIR}"
mkdir -p "$(dirname "${OUTPUT_FILE}")"

info "▶️  generating image"
info "    prompt: $PROMPT_FILE"
info "    output: $OUTPUT_FILE"
info "    steps:  $STEPS"

PYTHONPATH="${PYTHONPATH}" python -m sdxl_runner.from_file \
  --prompt-file "${PROMPT_FILE}" \
  --output "${OUTPUT_FILE}" \
  --steps "${STEPS}"

success "image written → ${OUTPUT_FILE}"
