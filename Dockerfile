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
RUN ARCH=$(dpkg --print-architecture | sed 's/amd64/x64/;s/arm64/arm64/') && \
    curl -sSL "https://github.com/gitleaks/gitleaks/releases/download/v8.30.0/gitleaks_8.30.0_linux_${ARCH}.tar.gz" \
    | tar xz -C /usr/local/bin gitleaks

# Install trivy
RUN ARCH=$(uname -m | sed 's/x86_64/64bit/;s/aarch64/ARM64/') && \
    curl -sSL "https://github.com/aquasecurity/trivy/releases/download/v0.69.3/trivy_0.69.3_Linux-${ARCH}.tar.gz" \
    | tar xz -C /usr/local/bin trivy

# Install checkov via pip
RUN pip install --no-cache-dir checkov

# Install PHP tools (psalm, local-php-security-checker)
# PHP runtime for psalm and enlightn
RUN apt-get update && apt-get install -y --no-install-recommends \
    php-cli \
    php-xml \
    php-mbstring \
    php-curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Composer + Psalm (global install)
ENV COMPOSER_HOME=/opt/composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer && \
    composer global require --no-interaction vimeo/psalm && \
    ln -s /opt/composer/vendor/bin/psalm /usr/local/bin/psalm && \
    chmod +x /opt/composer/vendor/bin/psalm

# local-php-security-checker
RUN ARCH=$(dpkg --print-architecture | sed 's/amd64/amd64/;s/arm64/arm64/') && \
    curl -sSL "https://github.com/fabpot/local-php-security-checker/releases/download/v2.1.3/local-php-security-checker_linux_${ARCH}" \
    -o /usr/local/bin/local-php-security-checker && \
    chmod +x /usr/local/bin/local-php-security-checker

# Install gosec
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/securego/gosec/releases/download/v2.25.0/gosec_2.25.0_linux_${ARCH}.tar.gz" \
    | tar xz -C /usr/local/bin gosec

# Install bandit via pip
RUN pip install --no-cache-dir bandit

# Install Ruby + Brakeman
RUN apt-get update && apt-get install -y --no-install-recommends ruby && \
    rm -rf /var/lib/apt/lists/* && \
    gem install brakeman -v '< 8' --no-document

# Install cargo-audit
RUN ARCH=$(uname -m | sed 's/x86_64/x86_64-unknown-linux-gnu/;s/aarch64/aarch64-unknown-linux-gnu/') && \
    curl -sSL "https://github.com/rustsec/rustsec/releases/download/cargo-audit%2Fv0.22.1/cargo-audit-${ARCH}-v0.22.1.tgz" \
    | tar xz --strip-components=1 -C /usr/local/bin "cargo-audit-${ARCH}-v0.22.1/cargo-audit"

# Install nuclei (DAST scanner) -- uses zip format, not tar.gz
ARG TARGETARCH
RUN curl -sSL "https://github.com/projectdiscovery/nuclei/releases/download/v3.7.1/nuclei_3.7.1_linux_${TARGETARCH}.zip" \
    -o /tmp/nuclei.zip && \
    unzip -o /tmp/nuclei.zip -d /usr/local/bin nuclei && \
    chmod +x /usr/local/bin/nuclei && \
    rm /tmp/nuclei.zip

# Bake Nuclei templates into image (runs as root, before USER switch)
# Templates stored in /root/.local/nuclei-templates/ then copied for scanner user
RUN nuclei -update-templates && \
    mkdir -p /home/scanner/.local && \
    cp -r /root/.local/nuclei-templates /home/scanner/.local/nuclei-templates

# Non-root user for security
RUN groupadd -r scanner && useradd -r -g scanner -d /app scanner
RUN mkdir -p /data && chown scanner:scanner /data
RUN chown -R scanner:scanner /home/scanner/.local

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
