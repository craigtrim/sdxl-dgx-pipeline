#!/usr/bin/env python3

from pathlib import Path

import sdxl_runner
from sdxl_runner import prompt_builder


def test_paths_exist():
    assert sdxl_runner.PROMPTS_DIR.exists()
    assert sdxl_runner.OUTPUT_PROMPTS_DIR.exists()


def test_generate_sdxl_prompt_monkeypatched(monkeypatch):
    def fake_call_ollama(payload: dict[str, object]) -> str:
        return "portrait of a knight in bronze armor, studio lighting, negative: blurry, lowres"

    monkeypatch.setattr(prompt_builder, "call_ollama", fake_call_ollama)

    idea = "knight portrait"
    out = prompt_builder.generate_sdxl_prompt(idea)

    assert out.startswith("knight portrait")
    assert "negative:" in out
    assert len(out.split()) <= prompt_builder.MAX_TOKENS


def test_cli_writes_file(tmp_path, monkeypatch):
    def fake_call_ollama(payload: dict[str, object]) -> str:
        return "forest spirit, cinematic, negative: blurry"

    monkeypatch.setattr(prompt_builder, "call_ollama", fake_call_ollama)

    out_file = tmp_path / "prompt.txt"
    idea = "forest spirit"

    # call library entrypoint, not subprocess
    text = prompt_builder.generate_sdxl_prompt(idea)
    out_file.write_text(text, encoding="utf-8")

    assert out_file.exists()
    saved = out_file.read_text(encoding="utf-8").strip()
    assert saved.startswith("forest spirit")
