# Nazara Development Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files and README (required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./

# Copy source code (needed for editable install)
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy remaining files
COPY sandbox/ ./sandbox/
COPY manage.py ./
COPY docker-entrypoint.sh ./
RUN chmod +x ./docker-entrypoint.sh

# Set Python path
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=sandbox.settings

ENTRYPOINT ["./docker-entrypoint.sh"]
