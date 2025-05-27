FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-setuptools \
    wget \
    git-lfs \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files from parent directory
COPY .. /app/
# Ensure rp_handler.py is in the right place
COPY ../rp_handler.py /app/rp_handler.py
COPY ../getting_started /app/getting_started/

# Install PyTorch first (compatible with CUDA 11.8)
RUN pip3 install --no-cache-dir \
    torch==2.2.2+cu118 \
    torchvision==0.17.2+cu118 \
    torchaudio==2.2.2+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118

# Install VERIFIED WORKING Hugging Face packages (compatible with lerobot)
RUN pip3 install --no-cache-dir \
    numpy==1.26.4 \
    huggingface-hub==0.25.2 \
    diffusers==0.26.3 \
    transformers==4.40.0 \
    accelerate==0.30.1 \
    peft==0.11.1

# Install other dependencies
RUN pip3 install --no-cache-dir \
    pillow \
    websockets \
    "networkx<3.2" \
    runpod

# Install remaining dependencies (excluding einops which lerobot will install)
RUN pip3 install --no-cache-dir \
    albumentations==1.4.18 \
    av==12.3.0 \
    h5py==3.12.1 \
    kornia==0.7.4 \
    matplotlib==3.10.0 \
    opencv-python==4.8.0.74 \
    omegaconf==2.3.0 \
    timm==1.0.14 \
    protobuf==3.20.3

# Install lerobot last (will install correct einops version)
RUN pip3 install --no-cache-dir lerobot

# Set Python path to include the app directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Download models
RUN git lfs install && \
    git clone --depth 1 https://huggingface.co/phospho-app/so100_strawberry_grape-915h3ndhhf /app/models

EXPOSE 8765

# Test that all imports work correctly
RUN python3 -c "import cv2; print('✅ OpenCV works')" && \
    python3 -c "import torch; print(f'✅ PyTorch works, CUDA available: {torch.cuda.is_available()}')" && \
    python3 -c "from huggingface_hub.errors import HFValidationError, RepositoryNotFoundError; print('✅ Hugging Face imports work')" && \
    python3 -c "import diffusers; import transformers; print('✅ Diffusers and Transformers work')" && \
    python3 -c "from getting_started.examples.eval_gr00t_so100 import handle_client; print('✅ GR00T imports work')"

# Verify files exist
RUN ls -la /app/ && \
    echo "Checking for rp_handler.py:" && \
    ls -la /app/rp_handler.py

# Run the RunPod handler
CMD ["python3", "-u", "/app/rp_handler.py"]