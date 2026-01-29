---
name: Create Sample Hatch Project with CalVer and Release Automation
overview: Create a minimal hatch-based Python project that demonstrates Calendar Versioning (YYYY.MM.DD.MICRO), version checking CLI, and automated PyPI release workflows. This will serve as a proof-of-concept to validate the approach before applying it to config-stash.
todos:
  - id: init-sample-project
    content: "Initialize sample hatch project: create directory, git repo, basic structure"
    status: pending
  - id: create-pyproject-toml
    content: Create pyproject.toml with hatch build system and dynamic versioning configuration
    status: pending
    dependencies:
      - init-sample-project
  - id: create-version-calc-script
    content: Create scripts/calc_version.py with CalVer version calculation logic
    status: pending
    dependencies:
      - init-sample-project
  - id: test-version-calc
    content: Test version calculation script with various scenarios (no tags, multiple tags, date boundaries)
    status: pending
    dependencies:
      - create-version-calc-script
  - id: create-version-cli
    content: Create version checking CLI tool (src/hatch_calver_sample/cli.py) with multiple commands
    status: pending
    dependencies:
      - init-sample-project
  - id: configure-dynamic-versioning
    content: "Configure hatch dynamic versioning (test different approaches: file, env, hook)"
    status: pending
    dependencies:
      - create-pyproject-toml
  - id: create-about-py
    content: Create __about__.py with dynamic version reading from importlib.metadata
    status: pending
    dependencies:
      - configure-dynamic-versioning
  - id: create-init-py
    content: Create __init__.py that imports __version__ from __about__.py
    status: pending
    dependencies:
      - create-about-py
  - id: create-release-workflow
    content: Create .github/workflows/release.yml for automated PyPI publishing
    status: pending
    dependencies:
      - configure-dynamic-versioning
  - id: create-tests
    content: Create unit tests for version calculation and CLI tool
    status: pending
    dependencies:
      - create-version-calc-script
      - create-version-cli
  - id: create-documentation
    content: Create README.md with complete documentation and usage examples
    status: pending
    dependencies:
      - create-version-calc-script
      - create-version-cli
      - create-release-workflow
  - id: test-complete-workflow
    content: "Test complete release workflow: tag creation → build → version verification → PyPI publish"
    status: pending
    dependencies:
      - create-release-workflow
      - create-tests
  - id: validate-pep440
    content: Validate PEP 440 compliance and version ordering across all scenarios
    status: pending
    dependencies:
      - create-version-calc-script
      - test-complete-workflow
  - id: create-makefile
    content: Create Makefile with convenient targets (version-calc, release-tag, etc.)
    status: pending
    dependencies:
      - create-version-calc-script
      - create-version-cli
---

# Plan: Sample Hatch Project with CalVer and Release Automation

## Overview

Create a minimal, working hatch-based Python project that demonstrates:

- Calendar Versioning (YYYY.MM.DD.MICRO) from git tags
- Dynamic versioning with hatch
- Version checking CLI tool
- Automated PyPI release via GitHub Actions
- Complete release workflow automation

This sample project will validate the CalVer implementation approach and serve as a reference for applying it to config-stash.

## Project Structure

### Sample Project Name

- **Project name**: `hatch-calver-sample` (or similar)
- **Package name**: `hatch_calver_sample`
- **Purpose**: Proof-of-concept for CalVer with hatch

### Directory Structure

```
hatch-calver-sample/
├── pyproject.toml              # Hatch configuration with dynamic versioning
├── README.md                   # Project documentation
├── CHANGELOG.md                # Changelog with CalVer format
├── LICENSE                     # License file
├── .github/
│   └── workflows/
│       └── release.yml         # Automated release workflow
├── scripts/
│   ├── calc_version.py         # Version calculation script
│   └── check_version.py        # Version checking CLI
├── src/
│   └── hatch_calver_sample/
│       ├── __init__.py         # Package with __version__
│       ├── __about__.py        # Version metadata
│       └── cli.py              # Version checking CLI implementation
└── tests/
    ├── __init__.py
    ├── test_version_calc.py    # Tests for version calculation
    └── test_version_cli.py     # Tests for CLI tool
```

## Phase 1: Initialize Sample Project

### 1.1 Project Setup

- Create new directory: `hatch-calver-sample`
- Initialize git repository
- Create basic `pyproject.toml` with hatch build system
- Set up minimal package structure

**Initial `pyproject.toml` structure:**

- Build system: `hatchling`
- Project metadata: name, description, readme, etc.
- Dynamic version configuration
- Script entry points for CLI tools

### 1.2 Basic Package Structure

- Create `src/hatch_calver_sample/` directory
- Create `__init__.py` with minimal exports
- Create `__about__.py` for version metadata
- Create `cli.py` for version checking commands

## Phase 2: Implement Version Calculation Script

### 2.1 Create Version Calculation Script

**File to create:**

- `scripts/calc_version.py`

**Requirements:**

- Calculate next CalVer version: `YYYY.MM.DD.MICRO`
- Query git tags matching CalVer pattern
- Find maximum MICRO for current date
- Increment MICRO or reset to 1 for new date
- Output version string: `YYYY.MM.DD.MICRO`
- Handle edge cases (no tags, invalid tags, etc.)

**Implementation details:**

- Use UTC date for consistency
- Support both `vYYYY.MM.DD.MICRO` and `YYYY.MM.DD.MICRO` tag formats
- Validate version format with regex
- PEP 440 compliance checks
- Command-line interface: `python scripts/calc_version.py`
- Optional flags: `--validate`, `--pep440-check`

### 2.2 Version Calculation Logic

```
1. Get current UTC date → YYYY.MM.DD
2. Fetch git tags (git fetch --tags)
3. Parse tags matching CalVer pattern
4. Filter tags with same date (YYYY.MM.DD)
5. Extract MICRO numbers
6. Calculate next MICRO = max(existing) + 1 or 1
7. Return: YYYY.MM.DD.MICRO
```

## Phase 3: Implement Version Checking CLI

### 3.1 CLI Tool Requirements

**File to create:**

- `scripts/check_version.py` or `src/hatch_calver_sample/cli.py`

**CLI Commands:**

- `version-calc`: Calculate next CalVer version
- `version-check`: Verify current version (from package or git)
- `version-validate`: Validate version format and PEP 440 compliance
- `version-compare`: Compare two versions
- `version-info`: Show version information (source, date, micro)

**CLI Features:**

- Multiple output formats: plain text, JSON
- Colorized output (optional)
- Validation with error messages
- Comparison with version operators (>, <, ==)
- Show version from different sources (package, git tag, VERSION file)

### 3.2 CLI Entry Point

**In `pyproject.toml`:**

```toml
[project.scripts]
calver-check = "hatch_calver_sample.cli:main"
# Or multiple commands
calver-version = "hatch_calver_sample.cli:version_cmd"
```

**CLI Usage examples:**

```bash
calver-check calc              # Calculate next version
calver-check check             # Check current version
calver-check validate 2024.01.18.1  # Validate version format
calver-check compare 2024.01.18.1 2024.01.18.2  # Compare versions
calver-check info              # Show version information
```

## Phase 4: Configure Dynamic Versioning with Hatch

### 4.1 Hatch Configuration Options

**Test different approaches:**

**Approach A: VERSION file**

```toml
[tool.hatch.version]
path = "src/hatch_calver_sample/VERSION"
```

- Script writes version to file
- Simple but requires file management

**Approach B: Environment variable**

```toml
[tool.hatch.version]
source = "env"
env = "HATCH_CALVER_VERSION"
```

- CI sets environment variable
- No file management needed

**Approach C: Custom build hook**

```toml
[tool.hatch.build.hooks]
custom = ["scripts.build_hook:set_version"]
```

- Custom Python script runs during build
- Most flexible but more complex

### 4.2 Version Metadata in Code

**File: `src/hatch_calver_sample/__about__.py`**

- Read version from `importlib.metadata`
- Fallback to VERSION file or environment variable
- Handle development builds gracefully

**File: `src/hatch_calver_sample/__init__.py`**

- Import `__version__` from `__about__.py`
- Export version for programmatic access

## Phase 5: Implement Release Workflow

### 5.1 GitHub Actions Workflow

**File to create:**

- `.github/workflows/release.yml`

**Workflow features:**

- Trigger on git tag push: `v*` pattern
- Extract version from tag (strip `v` prefix)
- Validate version format before building
- Build package with hatch
- Validate distributions with twine
- Publish to PyPI using Trusted Publishing or API token
- Create GitHub Release (optional)

**Workflow steps:**

1. Extract version from tag
2. Validate version format
3. Set version in build (via file/env/hook)
4. Install build dependencies
5. Build package: `hatch build`
6. Check distributions: `twine check dist/*`
7. Publish to PyPI
8. Generate release notes (optional)

### 5.2 Tag-based Release Process

1. Developer runs: `calver-check calc` → outputs `2024.01.18.1`
2. Create tag: `git tag v2024.01.18.1 -m "Release 2024.01.18.1"`
3. Push tag: `git push origin v2024.01.18.1`
4. GitHub Actions builds and publishes automatically

## Phase 6: Testing and Validation

### 6.1 Test Scenarios

**File to create:**

- `tests/test_version_calc.py`

**Test cases:**

- Version calculation with no tags → `YYYY.MM.DD.1`
- Version calculation with existing tags → correct MICRO increment
- Version calculation across date boundaries → MICRO resets
- Invalid tag formats → skipped gracefully
- PEP 440 compliance → valid versions
- Version ordering → newer > older

**File to create:**

- `tests/test_version_cli.py`

**CLI test cases:**

- `calc` command → outputs correct version
- `check` command → reads version correctly
- `validate` command → validates format correctly
- `compare` command → compares versions correctly
- `info` command → shows version information

### 6.2 Integration Testing

- End-to-end test: tag creation → build → version verification
- Test PEP 440 parsing and ordering
- Test build process with different version sources
- Test installation from built package

## Phase 7: Documentation and Examples

### 7.1 Project Documentation

**File to create:**

- `README.md`

**Sections:**

- Overview of CalVer implementation
- Installation instructions
- Version calculation usage
- CLI tool usage examples
- Release process documentation
- Configuration options explanation

### 7.2 Example Workflows

**Documented workflows:**

- Manual release process (tag → CI)
- Version calculation process
- Testing version locally
- Troubleshooting common issues

### 7.3 Configuration Documentation

- Explain different version source options
- Pros/cons of each approach
- Recommended approach with rationale
- Migration guide for other projects

## Phase 8: Release Automation Features

### 8.1 Makefile Targets

**File to create:**

- `Makefile`

**Targets:**

- `version-calc`: Calculate next version
- `version-check`: Check current version
- `version-validate`: Validate version format
- `release-tag`: Create and push release tag
- `build-test`: Build package for testing
- `test-release`: Test release process (dry-run)

### 8.2 Pre-commit Hooks (Optional)

- Validate version format in `pyproject.toml`
- Ensure `__version__` matches package version
- Check version consistency across files

## Phase 9: Validation Checklist

### 9.1 Functional Validation

- [ ] Version calculation works correctly
- [ ] CLI tool functions as expected
- [ ] Hatch builds package with correct version
- [ ] Version appears correctly in package metadata
- [ ] `__version__` in code matches package version
- [ ] PEP 440 compliance verified
- [ ] GitHub Actions workflow triggers on tag push
- [ ] Workflow validates and builds package
- [ ] Package publishes to PyPI successfully
- [ ] Package installs correctly from PyPI
- [ ] Version on PyPI matches git tag

### 9.2 Edge Case Testing

- [ ] No tags scenario
- [ ] Multiple tags same date
- [ ] Date boundary crossing
- [ ] Invalid tag formats
- [ ] Development builds (no git, no tags)
- [ ] Timezone handling (UTC consistency)

## Implementation Details

### Version Calculation Script Structure

**File: `scripts/calc_version.py`**

```python
#!/usr/bin/env python3
"""Calculate next CalVer version (YYYY.MM.DD.MICRO) from git tags."""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from typing import List, Optional, Tuple

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Calculate CalVer version")
    parser.add_argument("--validate", action="store_true", help="Validate version format")
    parser.add_argument("--pep440", action="store_true", help="Check PEP 440 compliance")
    args = parser.parse_args()

    version = calculate_next_version()

    if args.validate:
        if not validate_version_format(version):
            sys.exit(1)

    if args.pep440:
        if not check_pep440_compliance(version):
            sys.exit(1)

    print(version)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### CLI Tool Structure

**File: `src/hatch_calver_sample/cli.py`**

```python
"""CLI tool for CalVer version management."""

import argparse
import sys
from typing import Optional

def version_calc(args):
    """Calculate next version."""
    # Implementation

def version_check(args):
    """Check current version."""
    # Implementation

def version_validate(args):
    """Validate version format."""
    # Implementation

def version_compare(args):
    """Compare two versions."""
    # Implementation

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="CalVer version management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # calc command
    calc_parser = subparsers.add_parser("calc", help="Calculate next version")

    # check command
    check_parser = subparsers.add_parser("check", help="Check current version")

    # ... other commands

    args = parser.parse_args()

    if args.command == "calc":
        version_calc(args)
    elif args.command == "check":
        version_check(args)
    # ... handle other commands

    return 0
```

### Sample pyproject.toml Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "hatch-calver-sample"
dynamic = ["version"]
description = "Sample project demonstrating CalVer (YYYY.MM.DD.MICRO) with hatch"
readme = "README.md"
requires-python = ">=3.8"
license = { text = "MIT" }

[project.scripts]
calver-check = "hatch_calver_sample.cli:main"

[tool.hatch.version]
# Option A: VERSION file
path = "src/hatch_calver_sample/VERSION"
# Option B: Environment variable
# source = "env"
# env = "HATCH_CALVER_VERSION"
```

### Sample GitHub Actions Workflow

**File: `.github/workflows/release.yml`**

```yaml
name: Release to PyPI

on:
  push:
    tags:
         - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # For Trusted Publishing

    steps:
         - uses: actions/checkout@v4
        with:
          fetch-depth: 0

         - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

         - name: Extract version from tag
        id: version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          # Validate format
          if ! [[ "$VERSION" =~ ^[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[0-9]+$ ]]; then
            echo "Invalid CalVer format: $VERSION"
            exit 1
          fi

         - name: Set version
        run: |
          echo "${{ steps.version.outputs.version }}" > src/hatch_calver_sample/VERSION

         - name: Install build tools
        run: pip install hatchling build twine

         - name: Build package
        run: hatch build

         - name: Check package
        run: twine check dist/*

         - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist/
```

## Deliverables

### Core Components

1. **Version calculation script** (`scripts/calc_version.py`)

      - Calculates next CalVer version
      - Handles all edge cases
      - Validates version format

2. **Version checking CLI** (`src/hatch_calver_sample/cli.py`)

      - Multiple commands for version management
      - Version validation and comparison
      - Human-readable and JSON output

3. **Hatch configuration** (`pyproject.toml`)

      - Dynamic versioning setup
      - Working with chosen version source approach
      - All metadata configured

4. **Release workflow** (`.github/workflows/release.yml`)

      - Automated PyPI publishing
      - Version validation
      - Error handling

5. **Package code** (`src/hatch_calver_sample/`)

      - `__about__.py` with dynamic version
      - `__init__.py` exporting version
      - CLI implementation

### Documentation

1. **README.md** - Complete usage documentation
2. **CHANGELOG.md** - CalVer-formatted changelog example
3. **Inline code comments** - Explaining design decisions

### Tests

1. **Unit tests** - Version calculation and CLI tests
2. **Integration tests** - End-to-end release process tests
3. **Test documentation** - How to run tests

## Success Criteria

- [ ] Sample project builds successfully with hatch
- [ ] Version calculation script works correctly in all scenarios
- [ ] CLI tool provides all required commands
- [ ] Dynamic versioning works (version read from chosen source)
- [ ] Version appears correctly in built package
- [ ] GitHub Actions workflow publishes to PyPI
- [ ] Package installs from PyPI with correct version
- [ ] All tests pass
- [ ] Documentation is complete and clear
- [ ] Can be used as reference for config-stash implementation

## Testing Strategy

### Local Testing

1. Test version calculation with various tag scenarios
2. Test CLI commands locally
3. Test build process: `hatch build`
4. Test installation: `pip install -e .`
5. Test version reading: `python -c "import hatch_calver_sample; print(hatch_calver_sample.__version__)"`

### CI Testing

1. Test workflow with test tag (v2024.01.18.1)
2. Verify package builds correctly
3. Test publishing to TestPyPI first
4. Verify version consistency across build artifacts

### Validation Testing

1. Create test tags and verify MICRO increment
2. Test across date boundaries
3. Verify PEP 440 compliance
4. Test version ordering

## Files to Create

**Project files:**

- `pyproject.toml`
- `README.md`
- `CHANGELOG.md`
- `LICENSE`
- `.gitignore`
- `Makefile` (optional)

**Source code:**

- `src/hatch_calver_sample/__init__.py`
- `src/hatch_calver_sample/__about__.py`
- `src/hatch_calver_sample/cli.py`

**Scripts:**

- `scripts/calc_version.py`
- `scripts/check_version.py` (if separate from CLI)

**Workflows:**

- `.github/workflows/release.yml`

**Tests:**

- `tests/__init__.py`
- `tests/test_version_calc.py`
- `tests/test_version_cli.py`

## Notes

- Keep sample project minimal but complete
- Focus on demonstrating CalVer workflow, not package functionality
- Include extensive comments explaining why choices were made
- Document any limitations or trade-offs
- Make it easy to understand and adapt to config-stash

## Next Steps After Sample Project

Once sample project is validated:

1. Review what worked and what didn't
2. Identify any issues or limitations
3. Document lessons learned
4. Apply proven approach to config-stash
5. Adapt configuration as needed for config-stash's structure
