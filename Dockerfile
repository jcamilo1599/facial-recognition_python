# Base image with Python 3.10 (slim to keep image small)
FROM python:3.10-slim

# Prevent interactive prompts and ensure consistent pip behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# System dependencies for building native libs (dlib) and common image codecs
# - build-essential, cmake: required to build dlib from source
# - libopenblas-dev: BLAS for dlib
# - libjpeg-dev, zlib1g-dev: image codecs used by Pillow/opencv
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libopenblas-dev \
        libjpeg-dev \
        zlib1g-dev \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade build tooling before installing requirements
RUN python -m pip install --upgrade pip setuptools wheel

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy application source
COPY . .

# Default port for Cloud Run
ENV PORT=8080
EXPOSE 8080

# Start the FastAPI app using uvicorn
# Use the PORT environment variable provided by Cloud Run (defaults to 8080 locally)
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
