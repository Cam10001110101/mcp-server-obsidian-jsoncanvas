FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy project files
COPY . .

# Install dependencies and build project using uv
RUN /root/.cargo/bin/uv pip install --system .

# Create final image
FROM python:3.10-slim

WORKDIR /app

# Copy built files from builder
COPY --from=builder /app /app

# Create data directory
RUN mkdir -p /data/output

# Set environment variables
ENV OUTPUT_PATH=/data/output
ENV FORMAT=json

# Run the server
ENTRYPOINT ["python", "-m", "jsoncanvas"]
