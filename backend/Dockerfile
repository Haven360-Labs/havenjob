# HavenJob backend: Django + django-ninja
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies only (no project build; avoids needing README/packages here)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . .

# Entrypoint: migrate then start server
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
