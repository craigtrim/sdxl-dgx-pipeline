from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# single canonical location for prompts
PROMPTS_DIR = PROJECT_ROOT / "resources" / "prompts"
OUTPUT_PROMPTS_DIR = PROMPTS_DIR  # align

# images stay under output
OUTPUT_PNG_DIR = PROJECT_ROOT / "resources" / "output" / "png"
