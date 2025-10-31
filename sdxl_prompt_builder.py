#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sdxl_prompt_builder.py

Use local Ollama model `llama2-uncensored:latest` to turn a short user idea
into a hyper-detailed SDXL prompt.

Usage:
    python sdxl_prompt_builder.py --idea "a medieval scribe writing by candlelight" --out prompt.txt
    python sdxl_prompt_builder.py --idea-file idea.txt
"""

import argparse
import json
import sys
from pathlib import Path

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama2-uncensored:latest"


def read_idea(idea: str | None, idea_file: str | None) -> str:
    if idea:
        return idea.strip()
    if idea_file:
        p = Path(idea_file)
        if not p.exists():
            raise FileNotFoundError(f"idea file not found: {p}")
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"idea file is empty: {p}")
        return text
    raise ValueError("no idea provided; use --idea or --idea-file")


def build_system_instruction() -> str:
    # keep it tight: SDXL likes explicit camera, lighting, style, quality
    return (
        "You are a prompt engineer for Stable Diffusion XL (SDXL). "
        "Your job is to expand the user's brief idea into a single, highly descriptive prompt. "
        "Rules:\n"
        "1. ONE LINE ONLY.\n"
        "2. No meta-talk, no apologies, no explanations.\n"
        "3. Include subject, scene, composition, camera/shot, lighting, mood, style, quality tags.\n"
        "4. Prefer photographic language unless user clearly wants illustration.\n"
        "5. Add quality boosters like 'highly detailed, ultra sharp, 8k, studio lighting' when reasonable.\n"
        "6. Avoid trigger words that would violate platform rules.\n"
    )


def build_user_instruction(user_idea: str) -> str:
    return f"User idea: {user_idea}\nProduce SDXL prompt now:"


def call_ollama(payload: dict[str, object]) -> str:
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"ollama error: {resp.status_code} {resp.text}")

    # /api/generate can stream; here we assume non-stream or collect stream
    out: list[str] = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        data = json.loads(line)
        if "response" in data:
            out.append(data["response"])
        if data.get("done"):
            break
    return "".join(out).strip()


def generate_sdxl_prompt(user_idea: str) -> str:
    system_text = build_system_instruction()
    user_text = build_user_instruction(user_idea)

    payload: dict[str, object] = {
        "model": MODEL_NAME,
        "prompt": f"{system_text}\n{user_text}",
        "stream": True,
        # keep temp lower for consistency
        "options": {
            "temperature": 0.5,
            "top_p": 0.9,
        },
    }

    return call_ollama(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SDXL-ready prompt via Ollama")
    parser.add_argument("--idea", help="short idea text")
    parser.add_argument("--idea-file", help="file containing idea text")
    parser.add_argument("--out", default="prompt.txt", help="output file (default: prompt.txt)")
    args = parser.parse_args()

    try:
        idea = read_idea(args.idea, args.idea_file)
        sdxl_prompt = generate_sdxl_prompt(idea)
    except Exception as ex:
        # one-line JSON for logs
        print(json.dumps({"level": "error", "msg": str(ex)}))
        sys.exit(1)

    out_path = Path(args.out)
    out_path.write_text(sdxl_prompt, encoding="utf-8")
    print(json.dumps({"level": "info", "msg": "✅ SDXL prompt generated", "out": str(out_path)}))
    print(sdxl_prompt)


if __name__ == "__main__":
    main()
