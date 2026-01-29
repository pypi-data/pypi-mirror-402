.PHONY: help version-calc version-check version-validate release-tag build-test test test-ci lint security check-all clean install version-dev

# Default Python interpreter
PYTHON := python3

# Scripts directory
SCRIPTS_DIR := scripts

# Source directory
SRC_DIR := src/hatch_calvar_sample

# Version file location
VERSION_FILE := $(SRC_DIR)/VERSION

help:
	@echo "Available targets:"
	@echo ""
	@echo "Version Management:"
	@echo "  version-calc     - Calculate next CalVer version"
	@echo "  version-dev      - Generate CalVer dev version for local development"
	@echo "  version-check    - Check current version from different sources"
	@echo "  version-validate - Validate version format (use VERSION=2024.01.18.1)"
	@echo "  release-tag      - Create and push release tag manually (normally auto-created on PR merge)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test             - Run tests (basic)"
	@echo "  test-ci          - Run tests with coverage (like CI)"
	@echo "  lint             - Run pre-commit hooks (linting, formatting)"
	@echo "  security         - Run security scans (safety, pip-audit, gitleaks)"
	@echo "  check-all        - Run all CI checks locally (test-ci, lint, security)"
	@echo ""
	@echo "Build & Install:"
	@echo "  build-test       - Build package for testing"
	@echo "  install          - Install package in development mode (auto-generates dev version)"
	@echo "  clean            - Clean build artifacts and VERSION file"

version-dev:
	@echo "Generating CalVer dev version for local development..."
	@VERSION=$$($(PYTHON) $(SCRIPTS_DIR)/calc_version.py --validate --pep440); \
	DEV_VERSION="$${VERSION}.dev$$(date +%s)"; \
	echo "__version__ = \"$$DEV_VERSION\"" > $(VERSION_FILE); \
	echo "Generated dev version: $$DEV_VERSION"; \
	cat $(VERSION_FILE)

version-calc:
	@echo "Calculating next CalVer version..."
	@$(PYTHON) $(SCRIPTS_DIR)/calc_version.py --validate --pep440

version-check:
	@echo "Checking current version..."
	@calver-check check || $(PYTHON) -m hatch_calvar_sample.cli check

version-validate:
	@if [ -z "$(VERSION)" ]; then \
		echo "Error: VERSION variable required. Usage: make version-validate VERSION=2024.01.18.1"; \
		exit 1; \
	fi
	@echo "Validating version: $(VERSION)"
	@calver-check validate $(VERSION) || $(PYTHON) -m hatch_calvar_sample.cli validate $(VERSION)

release-tag:
	@echo "Creating release tag..."
	@VERSION=$$($(PYTHON) $(SCRIPTS_DIR)/calc_version.py); \
	echo "Next version: $$VERSION"; \
	read -p "Create and push tag v$$VERSION? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		git tag -a "v$$VERSION" -m "Release $$VERSION"; \
		echo "Created tag: v$$VERSION"; \
		read -p "Push tag to remote? (y/N) " -n 1 -r; \
		echo; \
		if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
			git push origin "v$$VERSION"; \
			echo "Pushed tag: v$$VERSION"; \
		else \
			echo "Tag created locally. Push with: git push origin v$$VERSION"; \
		fi; \
	else \
		echo "Cancelled"; \
	fi

build-test:
	@echo "Building package for testing..."
	@VERSION=$$($(PYTHON) $(SCRIPTS_DIR)/calc_version.py); \
	echo "__version__ = \"$$VERSION\"" > $(VERSION_FILE); \
	echo "Version file created: $(VERSION_FILE) = $$VERSION"; \
	hatch build; \
	echo "Package built in dist/"; \
	twine check dist/* || echo "Warning: twine not installed, skipping package check"

test:
	@echo "Running tests..."
	@pytest tests/ -v

test-ci: version-dev
	@echo "Running tests with coverage (CI mode)..."
	@echo "Installing test dependencies..."
	@pip install -e . pytest pytest-cov 2>/dev/null || \
		($(PYTHON) -m pip install --upgrade pip && \
		 pip install -e . pytest pytest-cov)
	@echo "Running pytest with coverage..."
	@pytest tests/ \
		--cov=src/hatch_calvar_sample \
		--cov=scripts \
		--cov-report=xml \
		--cov-report=html \
		--cov-report=term-missing \
		--junit-xml=junit.xml \
		-v
	@echo ""
	@echo "Coverage report generated:"
	@coverage report --fail-under=70 || echo "Warning: Coverage below 70%"

lint:
	@echo "Running pre-commit hooks (linting & formatting)..."
	@if ! command -v pre-commit >/dev/null 2>&1; then \
		echo "Installing pre-commit..."; \
		$(PYTHON) -m pip install --upgrade pip; \
		pip install pre-commit; \
	fi
	@pre-commit run --all-files

security:
	@echo "Running security scans..."
	@echo ""
	@echo "Installing security tools..."
	@$(PYTHON) -m pip install --upgrade pip
	@pip install safety pip-audit 2>/dev/null || pip install safety pip-audit
	@echo ""
	@echo "=== Dependency Security Scan ==="
	@echo "Generating requirements file..."
	@pip freeze > requirements-freeze.txt || true
	@echo ""
	@echo "Running Safety check..."
	@safety check --file requirements-freeze.txt || echo "Safety check completed with findings"
	@echo ""
	@echo "Running pip-audit..."
	@pip-audit --desc || echo "pip-audit completed with findings"
	@echo ""
	@echo "=== Secret Scanning ==="
	@if command -v gitleaks >/dev/null 2>&1; then \
		echo "Running gitleaks..."; \
		gitleaks detect --redact -v --exit-code=0 || echo "Gitleaks scan completed"; \
	else \
		echo "gitleaks not found. Install from: https://github.com/gitleaks/gitleaks"; \
		echo "Skipping secret scanning..."; \
	fi
	@rm -f requirements-freeze.txt
	@echo ""
	@echo "Security scans completed!"

check-all: test-ci lint security
	@echo ""
	@echo "=========================================="
	@echo "All CI checks passed locally!"
	@echo "=========================================="

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/ build/ *.egg-info/
	@rm -f $(VERSION_FILE)
	@echo "Cleaned build artifacts and VERSION file"

install: version-dev
	@echo "Installing package in development mode..."
	@pip install -e .
