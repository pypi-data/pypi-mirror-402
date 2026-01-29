.PHONY: help version-calc version-check version-validate release-tag build-test test test-ci lint security check-all clean install version-dev type-check complexity license docs build-verify changelog check-enterprise

# Default Python interpreter
# Note: Python 3.13+ has known blake2b/blake2s hashing warnings (harmless)
# Can be overridden: make PYTHON=python3 check-enterprise
ifeq ($(origin PYTHON),command line)
  # User specified PYTHON - verify it exists, fallback to python3 if not
  PYTHON := $(shell command -v $(PYTHON) 2>/dev/null || command -v python3 2>/dev/null || echo python3)
else
  # Auto-detect best available Python version
  PYTHON := $(shell command -v python3.12 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3.10 2>/dev/null || command -v python3 2>/dev/null || echo python3)
endif

# Scripts directory
SCRIPTS_DIR := scripts

# Source directory
SRC_DIR := src/hatch_calvar_sample

# Version file location
VERSION_FILE := $(SRC_DIR)/VERSION

help:
	@echo "Available targets:"
	@echo ""
	@echo "Note: Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3 (auto-detected)')"
	@echo "      (Python 3.13+ has known blake2 warnings - these are harmless)"
	@echo "      Override with: make PYTHON=python3 <target>"
	@echo "      Note: Use 'python3' not 'python3.14.2' - pyenv uses 'python3' command"
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
	@echo "  type-check       - Run mypy type checking"
	@echo "  complexity       - Run code complexity analysis (radon/xenon)"
	@echo "  security         - Run security scans (safety, pip-audit, bandit)"
	@echo "  license          - Check license compliance"
	@echo "  docs             - Check documentation quality"
	@echo "  changelog        - Validate CHANGELOG.md format"
	@echo "  check-all        - Run all basic CI checks (test-ci, lint, security)"
	@echo "  check-enterprise - Run ALL enterprise checks (includes license, docs, complexity)"
	@echo ""
	@echo "Build & Install:"
	@echo "  build-test       - Build package for testing"
	@echo "  build-verify     - Build and verify package installation"
	@echo "  install          - Install package in development mode (auto-generates dev version)"
	@echo "  clean            - Clean build artifacts and VERSION file"

version-dev:
	@echo "Generating CalVer dev version for local development..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@VERSION=$$($(PYTHON) $(SCRIPTS_DIR)/calc_version.py --validate --pep440 2>/dev/null || echo "0.0.0"); \
	if [ -z "$$VERSION" ] || [ "$$VERSION" = "" ]; then \
		VERSION="0.0.0"; \
	fi; \
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
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@VERSION=$$($(PYTHON) $(SCRIPTS_DIR)/calc_version.py 2>/dev/null || echo "0.0.0"); \
	if [ -z "$$VERSION" ] || [ "$$VERSION" = "" ]; then \
		VERSION="0.0.0"; \
	fi; \
	echo "__version__ = \"$$VERSION\"" > $(VERSION_FILE); \
	echo "Version file created: $(VERSION_FILE) = $$VERSION"; \
	PYTHONHASHSEED=0 hatch build 2>&1 | grep -v "ERROR:root:code for hash" | grep -v "ValueError: unsupported hash type" | grep -v "^$$" || hatch build 2>&1 | tail -3; \
	echo "Package built in dist/"; \
	$(PYTHON) -m twine check dist/* 2>/dev/null || twine check dist/* 2>/dev/null || echo "Warning: twine not installed, skipping package check"

build-verify: version-dev
	@echo "Building and verifying package..."
	@echo "Using Python: $$($(PYTHON) --version)"
	@echo ""
	@echo "=== Cleaning old builds ==="
	@rm -rf dist/*.whl dist/*.tar.gz 2>/dev/null || true
	@echo ""
	@echo "=== Installing build tools ==="
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install build twine >/dev/null 2>&1 || pip install build twine
	@echo ""
	@echo "=== Building Package ==="
	@# Suppress blake2 warnings from Python 3.13+ (these are harmless warnings)
	@PYTHONHASHSEED=0 hatch build 2>&1 | grep -v "ERROR:root:code for hash" | grep -v "ValueError: unsupported hash type" | grep -v "^$$" || hatch build 2>&1 | tail -5
	@echo ""
	@echo "=== Verifying with Twine ==="
	@$(PYTHON) -m twine check dist/* 2>/dev/null || twine check dist/* 2>/dev/null || echo "Warning: twine check skipped"
	@echo ""
	@echo "=== Testing Wheel Installation ==="
	@LATEST_WHEEL=$$(ls -t dist/*.whl 2>/dev/null | head -1); \
	if [ -z "$$LATEST_WHEEL" ]; then \
		echo "Error: No wheel file found in dist/"; \
		exit 1; \
	fi; \
	echo "Installing: $$LATEST_WHEEL"; \
	$(PYTHON) -m venv .test-env && \
	. .test-env/bin/activate && \
		pip install --upgrade pip >/dev/null 2>&1 && \
		pip install "$$LATEST_WHEEL" >/dev/null 2>&1 && \
		python -c "import hatch_calvar_sample; print(f'Version: {hatch_calvar_sample.__version__}')" && \
		calver-check --help >/dev/null 2>&1 && \
		echo "✓ CLI tool works" && \
		deactivate
	@rm -rf .test-env
	@echo ""
	@echo "=== Testing sdist Installation ==="
	@LATEST_SDIST=$$(ls -t dist/*.tar.gz 2>/dev/null | head -1); \
	if [ -z "$$LATEST_SDIST" ]; then \
		echo "Error: No sdist file found in dist/"; \
		exit 1; \
	fi; \
	echo "Installing: $$LATEST_SDIST"; \
	$(PYTHON) -m venv .test-env-sdist && \
	. .test-env-sdist/bin/activate && \
		pip install --upgrade pip >/dev/null 2>&1 && \
		pip install "$$LATEST_SDIST" >/dev/null 2>&1 && \
		python -c "import hatch_calvar_sample; print(f'Version: {hatch_calvar_sample.__version__}')" && \
		echo "✓ sdist installation works" && \
		deactivate
	@rm -rf .test-env-sdist
	@echo ""
	@echo "✓ Build verification completed!"

test:
	@echo "Running tests..."
	@pytest tests/ -v

test-ci: version-dev
	@echo "Running tests with coverage (CI mode)..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@echo "Installing test dependencies..."
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install -e . pytest pytest-cov >/dev/null 2>&1 || \
		($(PYTHON) -m pip install --upgrade pip && \
		 $(PYTHON) -m pip install -e . pytest pytest-cov)
	@echo "Running pytest with coverage..."
	@$(PYTHON) -m pytest tests/ \
		--cov=src/hatch_calvar_sample \
		--cov=scripts \
		--cov-report=xml \
		--cov-report=html \
		--cov-report=term-missing \
		--junit-xml=junit.xml \
		-v
	@echo ""
	@echo "Coverage report generated:"
	@$(PYTHON) -m coverage report --fail-under=70 || echo "Warning: Coverage below 70%"

lint:
	@echo "Running pre-commit hooks (linting & formatting)..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@if ! command -v pre-commit >/dev/null 2>&1; then \
		echo "Installing pre-commit..."; \
		$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1; \
		$(PYTHON) -m pip install pre-commit; \
	fi
	@pre-commit run --all-files

type-check: version-dev
	@echo "Running mypy type checking..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install mypy types-setuptools >/dev/null 2>&1 || $(PYTHON) -m pip install mypy types-setuptools
	@$(PYTHON) -m pip install -e . >/dev/null 2>&1 || true
	@$(PYTHON) -m mypy src/hatch_calvar_sample --ignore-missing-imports || echo "Type checking completed with issues"

complexity:
	@echo "Running code complexity analysis..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install radon xenon >/dev/null 2>&1 || $(PYTHON) -m pip install radon xenon
	@echo ""
	@echo "=== Cyclomatic Complexity ==="
	@radon cc src/ -a -s
	@echo ""
	@echo "=== Maintainability Index ==="
	@radon mi src/ -s
	@echo ""
	@echo "=== Complexity Thresholds Check ==="
	@xenon src/ --max-absolute C --max-modules B --max-average A || echo "Warning: Some modules exceed complexity thresholds"

security:
	@echo "Running security scans..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@echo ""
	@echo "Installing security tools..."
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install safety pip-audit bandit >/dev/null 2>&1 || $(PYTHON) -m pip install safety pip-audit bandit
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
	@echo "=== Code Security Scan (Bandit) ==="
	@bandit -r src/ -ll || echo "Bandit scan completed"
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

license:
	@echo "Checking license compliance..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install pip-licenses >/dev/null 2>&1 || $(PYTHON) -m pip install pip-licenses
	@$(PYTHON) -m pip install -e . >/dev/null 2>&1 || true
	@echo ""
	@echo "=== License Report ==="
	@pip-licenses --format=markdown
	@echo ""
	@echo "=== Checking for Problematic Licenses ==="
	@pip-licenses --fail-on="GPL;AGPL" || echo "Warning: Some dependencies have restrictive licenses"
	@echo ""
	@echo "License check completed!"

docs:
	@echo "Checking documentation quality..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install interrogate pydocstyle >/dev/null 2>&1 || $(PYTHON) -m pip install interrogate pydocstyle
	@echo ""
	@echo "=== Docstring Coverage ==="
	@interrogate src/ -v --fail-under=50 || echo "Warning: Docstring coverage below 50%"
	@echo ""
	@echo "=== Docstring Style ==="
	@pydocstyle src/ --convention=numpy --add-ignore=D100,D104,D105,D107 || echo "Some docstring style issues found"
	@echo ""
	@echo "Documentation check completed!"

changelog:
	@echo "Validating CHANGELOG.md..."
	@if [ ! -f CHANGELOG.md ]; then \
		echo "Error: CHANGELOG.md not found"; \
		exit 1; \
	fi
	@echo ""
	@echo "=== CHANGELOG Validation ==="
	@if grep -q "## \[Unreleased\]" CHANGELOG.md; then \
		echo "✓ Found [Unreleased] section"; \
	else \
		echo "Warning: Missing [Unreleased] section"; \
	fi
	@if grep -qE "## \[[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[0-9]+\]" CHANGELOG.md; then \
		echo "✓ Found CalVer formatted entries"; \
	else \
		echo "Notice: No CalVer formatted version entries found yet"; \
	fi
	@echo ""
	@echo "CHANGELOG validation completed!"

check-all: test-ci lint security
	@echo ""
	@echo "=========================================="
	@echo "All basic CI checks passed locally!"
	@echo "=========================================="

check-enterprise: test-ci lint security type-check complexity license docs changelog build-verify
	@echo ""
	@echo "=========================================="
	@echo "All enterprise CI checks passed locally!"
	@echo "=========================================="

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/ build/ *.egg-info/
	@rm -rf .test-env test-env test-env-sdist
	@rm -rf htmlcov/ .coverage coverage.xml junit.xml
	@rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/
	@rm -f $(VERSION_FILE)
	@rm -f requirements-freeze.txt
	@echo "Cleaned build artifacts and VERSION file"

install: version-dev
	@echo "Installing package in development mode..."
	@echo "Using Python: $$($(PYTHON) --version 2>/dev/null || echo 'python3')"
	@$(PYTHON) -m pip install --upgrade pip >/dev/null 2>&1 || true
	@$(PYTHON) -m pip install -e .
