#!/usr/bin/env python3

import argparse
from pathlib import Path

import torch
from diffusers import StableDiffusionXLPipeline

from sdxl_runner.config import (
    PROMPTS_DIR,
    OUTPUT_PNG_DIR,
)

MAX_TOKENS = 75  # SDXL/CLIP usually 77; reserve a couple


def read_prompt(path: str) -> str:
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        candidate = PROMPTS_DIR / p
        if candidate.exists():
            p = candidate

    if not p.exists():
        raise FileNotFoundError(f"prompt file not found: {p}")

    txt = p.read_text(encoding="utf-8").strip()
    if not txt:
        raise ValueError(f"prompt file is empty: {p}")
    return txt


def truncate_prompt(prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    parts = prompt.split()
    if len(parts) <= max_tokens:
        return prompt
    return " ".join(parts[:max_tokens])


def main() -> None:
    OUTPUT_PNG_DIR.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="SDXL image generator (prompt in file, length-safe)"
    )
    parser.add_argument(
        "--prompt-file",
        default=str(PROMPTS_DIR / "prompt.txt"),
        help="path to prompt file; relative paths are resolved under ./prompts/",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PNG_DIR / "out.png"),
        help="output PNG path; default is ./resources/output/png/out.png",
    )
    parser.add_argument("--steps", type=int, default=30)
    args = parser.parse_args()

    prompt_raw = read_prompt(args.prompt_file)
    prompt = truncate_prompt(prompt_raw, MAX_TOKENS)

    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        use_safetensors=True,
        variant="fp16",
    ).to("cuda")

    pipe.enable_attention_slicing()

    image = pipe(
        prompt,
        num_inference_steps=args.steps,
        guidance_scale=7.5,
    ).images[0]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)

    print(f"✅ wrote {out_path}")
    if prompt != prompt_raw:
        print(f"⚠️ prompt truncated to {MAX_TOKENS} tokens")


if __name__ == "__main__":
    main()
