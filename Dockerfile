FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and install
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen

# Copy application files
COPY . .

# Run the Panel app
CMD uv run panel serve ismip6_comparison_app/app.py \
    --address 0.0.0.0 \
    --port ${PORT} \
    --allow-websocket-origin="*" \
    --static-dirs static_content=./ismip6_comparison_app/static_content
