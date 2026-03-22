VERSION := $(shell python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])" 2>/dev/null || grep -m1 'version' pyproject.toml | cut -d'"' -f2)
PACKAGE_NAME := security-ai-scanner-$(VERSION)
REGISTRY ?= localhost
IMAGE_NAME ?= security-ai-scanner
BACKUP_DIR := backups
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

.DEFAULT_GOAL := help

.PHONY: help install run stop test verify-scanners migrate backup restore package clean docker-multiarch docker-push

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Build Docker images
	docker compose build

run: ## Start scanner (detached)
	@PID=$$(lsof -ti :8000 2>/dev/null); \
	if [ -n "$$PID" ]; then \
		echo "Port 8000 in use by PID $$PID — killing..."; \
		kill $$PID 2>/dev/null; sleep 1; \
		kill -9 $$PID 2>/dev/null || true; \
	fi
	docker compose up -d

stop: ## Stop scanner
	docker compose down
	@PID=$$(lsof -ti :8000 2>/dev/null); \
	if [ -n "$$PID" ]; then \
		echo "Port 8000 still in use by PID $$PID — killing..."; \
		kill $$PID 2>/dev/null; sleep 1; \
		kill -9 $$PID 2>/dev/null || true; \
	fi

test: ## Run test suite
	@if [ -f .venv/bin/pytest ]; then .venv/bin/pytest tests/ -v; elif python3 -c "import pytest" 2>/dev/null; then python3 -m pytest tests/ -v; else docker compose exec scanner python -m pytest tests/ -v; fi

verify-scanners: ## Smoke-test 12 scanners (11 binaries) inside Docker
	@echo "Verifying 12 scanners (11 binaries; Enlightn uses artisan, not a standalone binary)..."
	@docker compose exec -T scanner semgrep --version > /dev/null && echo "  semgrep: OK" || echo "  semgrep: FAIL"
	@docker compose exec -T scanner cppcheck --version > /dev/null && echo "  cppcheck: OK" || echo "  cppcheck: FAIL"
	@docker compose exec -T scanner gitleaks version > /dev/null && echo "  gitleaks: OK" || echo "  gitleaks: FAIL"
	@docker compose exec -T scanner trivy --version > /dev/null && echo "  trivy: OK" || echo "  trivy: FAIL"
	@docker compose exec -T scanner checkov --version > /dev/null && echo "  checkov: OK" || echo "  checkov: FAIL"
	@docker compose exec -T scanner psalm --version > /dev/null && echo "  psalm: OK" || echo "  psalm: FAIL"
	@docker compose exec -T scanner local-php-security-checker --help > /dev/null && echo "  php-security-checker: OK" || echo "  php-security-checker: FAIL"
	@docker compose exec -T scanner gosec --version 2>&1 | head -1 > /dev/null && echo "  gosec: OK" || echo "  gosec: FAIL"
	@docker compose exec -T scanner bandit --version > /dev/null && echo "  bandit: OK" || echo "  bandit: FAIL"
	@docker compose exec -T scanner brakeman --version > /dev/null && echo "  brakeman: OK" || echo "  brakeman: FAIL"
	@docker compose exec -T scanner cargo-audit --version > /dev/null && echo "  cargo-audit: OK" || echo "  cargo-audit: FAIL"
	@echo "Scanner verification complete."

migrate: ## Run database migrations
	docker compose exec scanner alembic upgrade head

backup: ## Backup DB, reports, and config to timestamped archive
	@mkdir -p $(BACKUP_DIR)
	@echo "Creating backup..."
	docker compose exec -T scanner sqlite3 /data/scanner.db ".backup '/tmp/scanner_backup.db'"
	docker compose cp scanner:/tmp/scanner_backup.db $(BACKUP_DIR)/scanner.db
	cp config.yml $(BACKUP_DIR)/config.yml 2>/dev/null || true
	docker compose cp scanner:/data/reports $(BACKUP_DIR)/reports 2>/dev/null || mkdir -p $(BACKUP_DIR)/reports
	tar czf $(BACKUP_DIR)/backup-$(TIMESTAMP).tar.gz -C $(BACKUP_DIR) scanner.db config.yml reports
	@rm -f $(BACKUP_DIR)/scanner.db $(BACKUP_DIR)/config.yml && rm -rf $(BACKUP_DIR)/reports
	@echo "Backup saved: $(BACKUP_DIR)/backup-$(TIMESTAMP).tar.gz"

restore: ## Restore from backup (usage: make restore BACKUP=path/to/file.tar.gz)
	@test -n "$(BACKUP)" || (echo "Usage: make restore BACKUP=path/to/file.tar.gz"; exit 1)
	@test -f "$(BACKUP)" || (echo "File not found: $(BACKUP)"; exit 1)
	@echo "Restoring from $(BACKUP)..."
	@mkdir -p /tmp/scanner-restore && tar xzf $(BACKUP) -C /tmp/scanner-restore
	docker compose cp /tmp/scanner-restore/scanner.db scanner:/data/scanner.db
	@cp /tmp/scanner-restore/config.yml ./config.yml 2>/dev/null || true
	docker compose cp /tmp/scanner-restore/reports scanner:/data/reports 2>/dev/null || true
	docker compose exec scanner alembic upgrade head
	@rm -rf /tmp/scanner-restore
	@echo "Restore complete. Run 'make migrate' if schema was updated."

package: ## Create distributable archive
	tar czf $(PACKAGE_NAME).tar.gz \
		--transform 's,^,$(PACKAGE_NAME)/,' \
		Dockerfile docker-compose.yml config.yml.example .env.example \
		README.md LICENSE CONTRIBUTING.md \
		src/ pyproject.toml alembic/ alembic.ini docs/
	@echo "Package created: $(PACKAGE_NAME).tar.gz"

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -f security-ai-scanner-*.tar.gz

docker-multiarch: ## Build multi-arch images (amd64 + arm64)
	docker buildx create --name multiarch --driver docker-container --use 2>/dev/null || docker buildx use multiarch
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(IMAGE_NAME):$(VERSION) \
		--output type=oci,dest=$(PACKAGE_NAME)-multiarch.tar .
	@echo "Multi-arch image saved: $(PACKAGE_NAME)-multiarch.tar"

docker-push: ## Push multi-arch images to registry
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(REGISTRY)/$(IMAGE_NAME):$(VERSION) --push .
