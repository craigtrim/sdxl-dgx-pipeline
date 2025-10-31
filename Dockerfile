FROM nvcr.io/nvidia/pytorch:25.02-py3

WORKDIR /workspace

# git so you can pull HF repos if needed
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

# Python deps for SDXL
RUN pip install --upgrade pip \
 && pip install \
      diffusers==0.35.2 \
      transformers==4.57.1 \
      accelerate==1.11.0 \
      safetensors \
      sentencepiece \
      huggingface_hub==0.36.0 \
      bitsandbytes

# bring in your scripts
COPY sdxl_from_file.py /workspace/sdxl_from_file.py
COPY generate-image.sh  /workspace/generate-image.sh
RUN chmod +x /workspace/generate-image.sh

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/workspace/.cache/huggingface

CMD ["/bin/bash"]
