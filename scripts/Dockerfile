FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-setuptools \
    wget \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY ../ /app
COPY pyproject.toml .

# Install PyTorch first (compatible with CUDA 11.8)
RUN pip3 install --no-cache-dir \
    torch==2.5.1+cu118 \
    torchvision==0.20.1+cu118 \
    torchaudio==2.5.1+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118

# Install other project dependencies first
RUN pip3 install --no-cache-dir \
    numpy \
    pillow \
    websockets \
    lerobot \
    "networkx<3.2" \
    runpod \
    huggingface-hub

# Install the project (this will install dependencies from pyproject.toml)
RUN pip3 install .

# Install compatible versions of huggingface packages
RUN pip3 install --no-cache-dir --force-reinstall \
    huggingface-hub==0.23.0 \
    diffusers==0.30.2 \
    transformers==4.45.2 \
    accelerate==1.2.1 \
    peft==0.14.0

# Download models
RUN git lfs install && \
    git clone --depth 1 https://huggingface.co/phospho-app/so100_strawberry_grape-915h3ndhhf /app/models

EXPOSE 8765

# Run the RunPod handler instead of the eval script directly
CMD ["python3", "-u", "rp_handler.py"]