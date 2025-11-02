FROM nvcr.io/nvidia/pytorch:25.02-py3

WORKDIR /workspace

# base deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# python deps
RUN pip install --upgrade pip \
    && pip install \
        diffusers==0.35.2 \
        transformers==4.57.1 \
        accelerate==1.11.0 \
        safetensors \
        sentencepiece \
        huggingface_hub==0.36.0

# project code
COPY src/ /workspace/src/
COPY scripts/ /workspace/scripts/
# do NOT copy prompts/ here
# do NOT copy resources/ here (your host mount will supply real data)

# create expected dirs so the script in the container never fails
RUN mkdir -p \
    /workspace/project/resources/prompts \
    /workspace/project/resources/output/prompts \
    /workspace/project/resources/output/png

ENV PYTHONPATH=/workspace/src

RUN chmod +x /workspace/scripts/generate-image.sh

CMD ["/bin/bash"]
