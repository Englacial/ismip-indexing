# Dockerfile for ISMIP6 Comparison Tool
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app.py config.yaml config_loader.py ./
COPY ismip6_index.py grid_utils.py ./
COPY table_a1_variables.yaml ismip6_experiments.yaml ./
COPY app_components ./app_components

# Create cache directory
RUN mkdir -p .cache

# Install Python dependencies
RUN uv sync --frozen

# Expose port (Cloud Run uses PORT environment variable)
ENV PORT=8080
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/app || exit 1

# Run the Panel app
# Use 0.0.0.0 to bind to all interfaces (required for Cloud Run)
# Use --allow-websocket-origin to accept connections from Cloud Run domain
# Note: In production, replace "*" with your specific Cloud Run domain
CMD uv run panel serve app.py \
    --address 0.0.0.0 \
    --port ${PORT} \
    --allow-websocket-origin="*"
