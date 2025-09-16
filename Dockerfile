FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV DB_PATH=/app/data/causal_memory.db
ENV PYTHONPATH=/app

# Expose port for MCP server (if needed for future HTTP mode)
EXPOSE 8000

# Default command runs the MCP server
CMD ["python", "src/mcp_server.py"]