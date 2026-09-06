FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyTgCalls (voice calls)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libffi-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY krytus/ ./krytus/

# Install dependencies
RUN uv sync --frozen --no-dev

# Run the bot
CMD ["uv", "run", "python", "-m", "krytus.main"]