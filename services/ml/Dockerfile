FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ../../requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy processing scripts
COPY ../../scripts/process_recording.py .
COPY ../../configs /app/configs

# Create directories
RUN mkdir -p /app/recordings /app/logs /app/models

# Set environment
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "-u", "process_recording.py"]
