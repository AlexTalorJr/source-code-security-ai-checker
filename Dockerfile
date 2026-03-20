FROM python:3.12-slim AS base

# System deps (curl for healthcheck, git for repo cloning,
# libpango/libharfbuzz for WeasyPrint PDF generation,
# cppcheck for C/C++ analysis)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    cppcheck \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

# Install semgrep via pip
RUN pip install --no-cache-dir semgrep

# Install gitleaks
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_${ARCH}.tar.gz" \
    | tar xz -C /usr/local/bin gitleaks

# Install trivy
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/aquasecurity/trivy/releases/download/v0.58.1/trivy_0.58.1_Linux-$(uname -m | sed 's/x86_64/64bit/;s/aarch64/ARM64/').tar.gz" \
    | tar xz -C /usr/local/bin trivy

# Install checkov via pip
RUN pip install --no-cache-dir checkov

# Non-root user for security
RUN groupadd -r scanner && useradd -r -g scanner -d /app scanner
RUN mkdir -p /data && chown scanner:scanner /data

WORKDIR /app

# Copy source and install
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# App config and migrations
COPY alembic.ini .
COPY alembic/ alembic/
COPY config.yml.example config.yml

# Copy gitleaks ignore file
COPY .gitleaksignore .

# Set ownership
RUN chown -R scanner:scanner /app

USER scanner

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "scanner.main:app", "--host", "0.0.0.0", "--port", "8000"]
