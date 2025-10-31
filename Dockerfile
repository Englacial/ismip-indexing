FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and install
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy application files
COPY . .

# Run the Panel app
CMD uv run panel serve app.py \
    --address 0.0.0.0 \
    --port ${PORT} \
    --allow-websocket-origin="*"
