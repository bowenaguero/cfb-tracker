FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git

# Copy dependency files
COPY uv.lock pyproject.toml README.md ./

# Copy source code
COPY src ./src

# Sync the project
RUN uv sync

# Install cfb-cli from private repo (GH_PAT passed at runtime or build)
ARG GH_PAT
RUN if [ -n "$GH_PAT" ]; then \
    uv pip install git+https://${GH_PAT}@github.com/bowenaguero/cfb-cli.git; \
    fi

RUN uv run playwright install --with-deps

CMD ["uv", "run", "python", "-m", "cfb_tracker.main"]
