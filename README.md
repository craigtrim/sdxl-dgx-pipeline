# SDXL on NVIDIA Sparx (GB10)

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![CUDA](https://img.shields.io/badge/CUDA-12.x-green.svg)
![Diffusers](https://img.shields.io/badge/diffusers-0.35.2-purple.svg)
![Docker](https://img.shields.io/badge/docker-required-informational.svg)
![GPU](https://img.shields.io/badge/GPU-NVIDIA%20GB10-critical.svg)

Run SDXL in a Docker container, generate prompts with a local Ollama model, and write images to the host.

## Files

- `Dockerfile`
  - Base image: `nvcr.io/nvidia/pytorch:25.02-py3`
  - Installs: diffusers, transformers, accelerate, safetensors, sentencepiece, huggingface_hub, bitsandbytes
  - Copies in `sdxl_from_file.py` and `generate-image.sh`

- `sdxl_prompt_builder.py`
  - Runs on the host
  - Calls Ollama at `http://localhost:11434`
  - Uses `llama2-uncensored:latest` to expand a short idea into a detailed SDXL prompt
  - Writes the prompt to a file

- `sdxl_from_file.py`
  - Runs inside the container
  - Reads a prompt from a file
  - Loads `stabilityai/stable-diffusion-xl-base-1.0` with fp16
  - Saves a PNG

- `generate-image.sh`
  - Runs inside the container
  - Thin wrapper around `sdxl_from_file.py` for `docker run` parameters

- `build-and-run-sdxl.sh`
  - Host entrypoint
  - Build → prompt → MD5 file name → `docker run` (with GB10 flags)

## Prerequisites

1. Docker with NVIDIA runtime on the Sparx unit
2. Ollama running locally:
   '''
   ollama pull llama2-uncensored
   '''
   or
   '''
   ollama run llama2-uncensored
   '''
3. A host directory for outputs, for example:
   '''
   /home/sdxl
   └── prompts
   '''

Update paths in the scripts if using a different directory.

## Directory convention

Default in the scripts:
- host data dir: `/home/craigtrim/sdxl`
- container mount: `/workspace/data`

Adjust to:
- host: `/home/<user>/sdxl`
- container: `/workspace/data`

## Build and run

From the project directory:
'''
./build-and-run-sdxl.sh "generate HMS Surprise sailing around Cape Horn in 1815"
'''

This performs:

1. Build:
   '''
   sudo docker build -t sdxl:local .
   '''
2. Prompt generation:
   '''
   python /home/<user>/projects/sdxl/sdxl_prompt_builder.py \
     --idea "<your idea>" \
     --out /home/<user>/sdxl/prompts/tmp.txt
   '''
3. MD5 naming:
   - prompt → `/home/<user>/sdxl/prompts/<md5>.txt`
   - image → `/home/<user>/sdxl/<md5>.png`
4. Container run with recommended flags:
   '''
   sudo docker run -it --gpus all \
     --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
     -v /home/<user>/sdxl:/workspace/data \
     sdxl:local \
     /workspace/generate-image.sh \
       --prompt-file /workspace/data/prompts/<md5>.txt \
       --output /workspace/data/<md5>.png
   '''

Because of the bind mount, the PNG is written directly to the host directory.

## Notes

- `xformers` is not installed in this image. Use attention slicing in diffusers.
- Rebuild the image after changing:
  - `Dockerfile`
  - `sdxl_from_file.py`
  - `generate-image.sh`
- Keep the runtime flags for GB10:
  '''
  --ipc=host --ulimit memlock=-1 --ulimit stack=67108864
  '''

## Variants

Generate the prompt only:
'''
python sdxl_prompt_builder.py \
  --idea "dieselpunk airship" \
  --out /home/<user>/sdxl/prompts/test.txt
'''

Use an existing prompt:
'''
sudo docker run -it --gpus all \
  --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 \
  -v /home/<user>/sdxl:/workspace/data \
  sdxl:local \
  /workspace/generate-image.sh \
    --prompt-file /workspace/data/prompts/test.txt \
    --output /workspace/data/test.png
'''
