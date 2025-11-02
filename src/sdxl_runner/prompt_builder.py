#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys
from pathlib import Path

import requests

from sdxl_runner.config import (
    PROMPTS_DIR,
    OUTPUT_PROMPTS_DIR,
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama2-uncensored:latest"
MAX_TOKENS = 77
BASE_NEGATIVE_BLOCK = "negative: blurry, lowres, deformed, watermark, text, logo"
BASE_NEGATIVE_TOKENS = BASE_NEGATIVE_BLOCK.split()


def read_idea(idea: str | None, idea_file: str | None) -> str:
    if idea:
        return idea.strip()
    if idea_file:
        p = Path(idea_file)
        if not p.is_absolute() and not p.exists():
            candidate = PROMPTS_DIR / p
            if candidate.exists():
                p = candidate
        if not p.exists():
            raise FileNotFoundError(f"idea file not found: {p}")
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"idea file is empty: {p}")
        return text
    raise ValueError("no idea provided; use --idea or --idea-file")


def build_system_instruction() -> str:
    return (
        "You are an SDXL prompt expander.\n"
        "INPUT: a very short user hint about an image.\n"
        "TASK: expand the hint into ONE single-line SDXL-ready prompt suitable for Stable Diffusion XL 1.0.\n"
        "HARD RULES:\n"
        "1. Do NOT remove user concepts. You may ADD detail, but you may NOT drop what the user asked for.\n"
        "2. Output the prompt only. No explanations. No quotes. No markdown.\n"
        "3. Keep it concise; target 85-90 words so it fits a 77-token cap after postprocessing.\n"
        "4. Always specify (in this order): subject, location/context, composition/camera, lighting, style, quality, negatives.\n"
        "5. Prefer photorealistic and highly detailed.\n"
        "6. Always include a negatives segment starting with 'negative:'. If you must shorten, shorten the negatives first.\n"
        "STRUCTURE:\n"
        "<subject>, <location/context>, <composition/camera>, <lighting>, <style>, <quality>, negative: blurry, lowres, deformed, watermark, text, logo\n"
        "EXAMPLE:\n"
        "photorealistic, highly detailed ultra sharp, negative: blurry, lowres, deformed, watermark, text, logo\n"
        "NOW EXPAND THIS HINT:\n"
    )


def build_user_instruction(user_idea: str) -> str:
    return user_idea.strip()


def call_ollama(payload: dict[str, object]) -> str:
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"ollama error: {resp.status_code} {resp.text}")

    fragments: list[str] = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        data = json.loads(line)
        if "response" in data:
            fragments.append(data["response"])
        if data.get("done"):
            break
    return "".join(fragments).strip()


def normalize_ws(text: str) -> str:
    return " ".join(text.split())


def rebuild_with_negatives(prefix_tokens: list[str], body_tokens: list[str], max_tokens: int) -> list[str]:
    base_len = len(prefix_tokens) + len(body_tokens)
    room = max_tokens - base_len
    if room <= 0:
        return (prefix_tokens + body_tokens)[:max_tokens]

    if room >= len(BASE_NEGATIVE_TOKENS):
        return prefix_tokens + body_tokens + BASE_NEGATIVE_TOKENS

    neg_tokens = BASE_NEGATIVE_TOKENS[:room]
    if "negative:" not in neg_tokens:
        neg_tokens = ["negative:"] + neg_tokens[:-1] if len(neg_tokens) > 0 else ["negative:"]
    return prefix_tokens + body_tokens + neg_tokens


def enforce_token_cap(user_idea: str, model_text: str, max_tokens: int = MAX_TOKENS) -> str:
    user_idea = normalize_ws(user_idea)
    model_text = normalize_ws(model_text)

    user_tokens = user_idea.split()
    model_tokens = model_text.split()

    i = 0
    while i < len(user_tokens) and i < len(model_tokens) and user_tokens[i].lower() == model_tokens[i].lower():
        i += 1
    model_tail = model_tokens[i:]

    merged = user_tokens + model_tail

    if "negative:" in merged:
        if len(merged) <= max_tokens:
            return " ".join(merged)
        allowed_tail = max_tokens - len(user_tokens)
        if allowed_tail < 0:
            return " ".join(user_tokens[:max_tokens])
        final_tokens = user_tokens + merged[len(user_tokens):len(user_tokens) + allowed_tail]
        return " ".join(final_tokens)

    content_tokens = merged[len(user_tokens):]
    rebuilt = rebuild_with_negatives(user_tokens, content_tokens, max_tokens)
    return " ".join(rebuilt)


def generate_sdxl_prompt(user_idea: str) -> str:
    system_text = build_system_instruction()
    user_text = build_user_instruction(user_idea)

    payload: dict[str, object] = {
        "model": MODEL_NAME,
        "prompt": f"{system_text}{user_text}",
        "stream": True,
        "options": {
            "temperature": 0.35,
            "top_p": 0.9,
        },
    }

    raw = call_ollama(payload)
    final_prompt = enforce_token_cap(user_idea, raw, MAX_TOKENS)
    return final_prompt


def main() -> None:
    OUTPUT_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Generate SDXL-ready prompt via Ollama (77-token capped, user-idea preserved)"
    )
    parser.add_argument("--idea", help="short idea text")
    parser.add_argument(
        "--idea-file",
        help="file containing idea text; relative paths are resolved under ./prompts/",
    )
    parser.add_argument(
        "--out",
        default=str(OUTPUT_PROMPTS_DIR / "prompt.txt"),
        help="output file (default: ./resources/output/prompts/prompt.txt)",
    )
    args = parser.parse_args()

    try:
        idea = read_idea(args.idea, args.idea_file)
        sdxl_prompt = generate_sdxl_prompt(idea)
    except Exception as ex:
        print(json.dumps({"level": "error", "msg": str(ex)}))
        sys.exit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(sdxl_prompt, encoding="utf-8")
    print(json.dumps({"level": "info", "msg": "✅ SDXL prompt generated", "out": str(out_path)}))
    print(sdxl_prompt)


if __name__ == "__main__":
    main()
