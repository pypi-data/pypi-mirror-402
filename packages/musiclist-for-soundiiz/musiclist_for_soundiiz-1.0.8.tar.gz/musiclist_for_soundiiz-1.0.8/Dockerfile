# MusicList for Soundiiz - Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio file processing
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY setup.py .
COPY README.md .
COPY LICENSE .

# Install the package
RUN pip install --no-cache-dir -e .

# Create mount point for music directory
VOLUME ["/music"]

# Create mount point for output directory
VOLUME ["/output"]

# Set default output directory
ENV OUTPUT_DIR=/output

# Default command (can be overridden)
ENTRYPOINT ["musiclist-for-soundiiz"]

# Default arguments
CMD ["--help"]

# Labels
LABEL maintainer="lucmuss"
LABEL description="Extract music metadata for Soundiiz import"
LABEL version="1.0.0"
