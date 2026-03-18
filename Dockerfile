FROM python:3.12-slim AS base

# System deps (curl for healthcheck, git for Phase 2 repo cloning)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN groupadd -r scanner && useradd -r -g scanner -d /app scanner
RUN mkdir -p /data && chown scanner:scanner /data

WORKDIR /app

# Python deps first (Docker cache layer)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# App code
COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/
COPY config.yml.example config.yml

# Set ownership
RUN chown -R scanner:scanner /app

USER scanner

EXPOSE 8000

CMD ["uvicorn", "scanner.main:app", "--host", "0.0.0.0", "--port", "8000"]
