FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY uv.lock pyproject.toml README.md ./

# Copy source code
COPY src ./src

# Sync the project
RUN uv sync

# Worker doesn't need cfb-cli or Playwright - it just processes queue jobs

CMD uv run rq worker social-posts --url $REDIS_URL
