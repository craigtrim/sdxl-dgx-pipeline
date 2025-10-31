#!/usr/bin/env python3
from diffusers import StableDiffusionXLPipeline
import torch
import argparse
from pathlib import Path


def read_prompt(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"prompt file not found: {p}")
    txt = p.read_text(encoding="utf-8").strip()
    if not txt:
        raise ValueError(f"prompt file is empty: {p}")
    return txt


def main() -> None:
    parser = argparse.ArgumentParser(description="SDXL image generator (prompt in file)")
    parser.add_argument("--prompt-file", default="prompt.txt")
    parser.add_argument("--output", default="out.png")
    parser.add_argument("--steps", type=int, default=30)
    args = parser.parse_args()

    prompt = read_prompt(args.prompt_file)

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

    image.save(args.output)
    print(f"✅ wrote {args.output} from {args.prompt_file}")


if __name__ == "__main__":
    main()
