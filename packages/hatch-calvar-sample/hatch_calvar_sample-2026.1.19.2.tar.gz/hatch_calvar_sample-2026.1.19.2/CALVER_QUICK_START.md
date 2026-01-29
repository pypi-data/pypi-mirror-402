# CalVer Quick Start Checklist

Use this quick checklist when adding CalVer to a new project.

## Files to Copy

- [ ] `scripts/calc_version.py` → `your-project/scripts/calc_version.py`
- [ ] `.github/workflows/auto-tag.yml` → `your-project/.github/workflows/auto-tag.yml`
- [ ] `.github/workflows/release.yml` → `your-project/.github/workflows/release.yml`

## Configuration Changes

### pyproject.toml

```toml
[project]
dynamic = ["version"]  # Add this

[tool.hatch.version]
path = "src/<your-package>/VERSION"  # Add this section
```

### Workflows - Update These Values

**auto-tag.yml:**
- [ ] Branch names (if not main/master)
- [ ] Python version (if not 3.11)
- [ ] Script path (if scripts in different location)

**release.yml:**
- [ ] Workflow name in `workflow_run.workflows` (must match auto-tag.yml name)
- [ ] Package path: `src/<your-package>/VERSION`
- [ ] Python version (if not 3.11)
- [ ] Environment name (must match PyPI config)

### Git Configuration

- [ ] Create `src/<your-package>/VERSION` with dev version
- [ ] Add `src/<your-package>/VERSION` to `.gitignore`

## PyPI Configuration

1. [ ] Go to PyPI → Project → Manage → Publishing → Trusted Publishers
2. [ ] Add GitHub Actions publisher:
   - Owner: `your-github-username`
   - Repository: `your-repo-name`
   - Workflow filename: `release.yml`
   - Environment name: `pypi` (if using environment)
3. [ ] Verify publisher is "Active" (after first publish)

## Testing Steps

1. [ ] `python scripts/calc_version.py` - Should output CalVer version
2. [ ] `make version-dev` (or manual) - Generate dev version
3. [ ] `pip install -e .` - Install in dev mode
4. [ ] Merge PR → Verify tag created
5. [ ] Verify release workflow runs
6. [ ] Check PyPI for new version

## Key Commands

```bash
# Calculate next version
python scripts/calc_version.py

# Generate dev version
make version-dev

# Install in dev mode (auto-generates version)
make install

# Manual installation
pip install -e .

# Check version
python -c "from <your-package> import __version__; print(__version__)"
```

## Common Issues

| Issue | Quick Fix |
|-------|-----------|
| VERSION file missing | Run `make version-dev` or create manually |
| Workflow doesn't trigger | Check workflow files are on default branch |
| PyPI invalid-publisher | Verify Trusted Publisher config matches workflow |
| Version format error | Ensure VERSION has `__version__ = "..."` format |

## Reference Files

For detailed explanations, see `CALVER_MIGRATION_GUIDE.md`.
