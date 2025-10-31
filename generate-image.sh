#!/usr/bin/env bash
set -euo pipefail

# 🎯 small wrapper so docker can call python easily

PROMPT_FILE="prompt.txt"
OUTPUT_FILE="out.png"
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
  error "prompt file not found: $PROMPT_FILE"
  exit 1
fi

info "▶️  generating image"
info "    prompt: $PROMPT_FILE"
info "    output: $OUTPUT_FILE"
info "    steps:  $STEPS"

python /workspace/sdxl_from_file.py \
  --prompt-file "$PROMPT_FILE" \
  --output "$OUTPUT_FILE" \
  --steps "$STEPS"

success "image written → $OUTPUT_FILE"

