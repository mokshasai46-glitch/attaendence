FROM python:3.11-slim

# Install system libraries and compilers required for dlib / face_recognition compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gfortran \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose port 7860 as expected by Hugging Face Spaces
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860"]
