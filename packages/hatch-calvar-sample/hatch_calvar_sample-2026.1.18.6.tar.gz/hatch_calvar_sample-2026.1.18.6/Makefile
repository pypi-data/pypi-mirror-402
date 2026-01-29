.PHONY: help version-calc version-check version-validate release-tag build-test test clean install

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
	@echo "  version-calc     - Calculate next CalVer version"
	@echo "  version-check    - Check current version from different sources"
	@echo "  version-validate - Validate version format (use VERSION=2024.01.18.1)"
	@echo "  release-tag      - Create and push release tag manually (normally auto-created on PR merge)"
	@echo "  build-test       - Build package for testing"
	@echo "  test             - Run tests"
	@echo "  install          - Install package in development mode"
	@echo "  clean            - Clean build artifacts and VERSION file"

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
	echo "$$VERSION" > $(VERSION_FILE); \
	echo "Version file created: $(VERSION_FILE) = $$VERSION"; \
	hatch build; \
	echo "Package built in dist/"; \
	twine check dist/* || echo "Warning: twine not installed, skipping package check"

test:
	@echo "Running tests..."
	@pytest tests/ -v

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/ build/ *.egg-info/
	@rm -f $(VERSION_FILE)
	@echo "Cleaned build artifacts and VERSION file"

install:
	@echo "Installing package in development mode..."
	@pip install -e .
