# Build stage - Install dependencies with PyTorch CPU-only
FROM python:3.12-slim AS builder

WORKDIR /app

# Install only necessary build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install PyTorch CPU-only from specific index to avoid CUDA
# This reduces PyTorch from ~2GB to ~200MB
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage - Create minimal production image
FROM python:3.12-slim

WORKDIR /app

# Copy only Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV DB_PATH=/app/data/causal_memory.db
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose port
EXPOSE 8000

# Copy startup script
COPY start_server.sh /app/start_server.sh
RUN chmod +x /app/start_server.sh

# Run server (will choose REST API or MCP based on SERVICE_TYPE env var)
CMD ["/app/start_server.sh"]
