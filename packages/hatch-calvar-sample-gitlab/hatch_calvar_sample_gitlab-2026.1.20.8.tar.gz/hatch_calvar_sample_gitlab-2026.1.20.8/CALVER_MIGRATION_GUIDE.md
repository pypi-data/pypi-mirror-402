# CalVer Migration Guide: Reusing CalVer Workflow in Other Projects

This guide explains how to adapt the CalVer versioning and automated release workflow from `hatch-calvar-sample-gitlab` to your own Python projects.

## Overview

This guide helps you set up:
- **Calendar Versioning (CalVer)** with format `YYYY.MM.DD.MICRO`
- **Automated tag creation** on PR merge
- **Automated PyPI publishing** via GitLab CI/CD
- **Dynamic versioning** with hatch
- **Local development** with CalVer dev versions

## Prerequisites

1. Python project using **hatch** as build backend (or willing to migrate)
2. Project published to **PyPI** (or planning to publish)
3. **GitLab CI/CD** enabled for the repository
4. Basic familiarity with:
   - Git and GitLab
   - Python packaging (hatch/pip)
   - GitLab CI/CD pipelines

## Quick Start Checklist

- [ ] Copy required files (scripts, workflows)
- [ ] Update `pyproject.toml` configuration
- [ ] Configure PyPI Trusted Publishing
- [ ] Test version calculation locally
- [ ] Test workflow triggers
- [ ] Verify PyPI publishing

---

## Step 1: Copy Required Files

### 1.1 Copy Version Calculation Script

Copy the version calculation script to your project:

```bash
# From hatch-calvar-sample-gitlab
cp scripts/calc_version.py <your-project>/scripts/calc_version.py
chmod +x <your-project>/scripts/calc_version.py
```

**Key points:**
- Script calculates next CalVer version from git tags
- Uses UTC date for consistency
- Supports both `vYYYY.MM.DD.MICRO` and `YYYY.MM.DD.MICRO` tag formats
- Validates CalVer format and PEP 440 compliance

### 1.2 Copy GitHub Actions Workflows

Copy both workflow files:

```bash
# Create workflows directory if it doesn't exist
mkdir -p <your-project>/.github/workflows

# Copy workflows
cp .github/workflows/auto-tag.yml <your-project>/.github/workflows/auto-tag.yml
cp .github/workflows/release.yml <your-project>/.github/workflows/release.yml
```

**Important:** Update workflow names and paths in these files (see Step 2.2).

### 1.3 Update Makefile (Optional)

If you use a Makefile, add these targets:

```makefile
.PHONY: version-calc version-dev install

PYTHON := python3
SCRIPTS_DIR := scripts
SRC_DIR := src/<your-package-name>
VERSION_FILE := $(SRC_DIR)/VERSION

version-calc:
	@echo "Calculating next CalVer version..."
	@$(PYTHON) $(SCRIPTS_DIR)/calc_version.py --validate --pep440

version-dev:
	@echo "Generating CalVer dev version for local development..."
	@VERSION=$$($(PYTHON) $(SCRIPTS_DIR)/calc_version.py --validate --pep440); \
	DEV_VERSION="$${VERSION}.dev$$(date +%s)"; \
	echo "__version__ = \"$$DEV_VERSION\"" > $(VERSION_FILE); \
	echo "Generated dev version: $$DEV_VERSION"; \
	cat $(VERSION_FILE)

install: version-dev
	@echo "Installing package in development mode..."
	@pip install -e .
```

---

## Step 2: Update Configuration Files

### 2.1 Update `pyproject.toml`

Add/update these sections in your `pyproject.toml`:

```toml
[project]
name = "your-package-name"
dynamic = ["version"]  # Required for dynamic versioning
# ... other project metadata ...

[tool.hatch.version]
path = "src/<your-package-name>/VERSION"
```

**Key changes:**
- Add `dynamic = ["version"]` to `[project]` section
- Add `[tool.hatch.version]` section pointing to VERSION file path
- Update path to match your package structure

### 2.2 Update Workflow Files

#### Update `auto-tag.yml`:

1. **Workflow name** (if different):
   ```yaml
   name: Auto-create Release Tag  # Change if desired
   ```

2. **Branch names** (if not main/master):
   ```yaml
   branches:
     - main
     - master
     # Add your default branch names
   ```

3. **Python version** (if different):
   ```yaml
   python-version: "3.11"  # Update to your preferred version
   ```

4. **Script path** (if scripts are in different location):
   ```yaml
   VERSION=$(python scripts/calc_version.py --validate --pep440)
   ```

#### Update `release.yml`:

1. **Workflow name** (for workflow_run trigger):
   ```yaml
   name: Release to PyPI  # Must match when referenced

   workflow_run:
     workflows: ["Auto-create Release Tag"]  # Must match auto-tag.yml name
   ```

2. **Package path**:
   ```yaml
   echo "__version__ = \"${{ steps.version.outputs.version }}\"" > src/<your-package>/VERSION
   ```

3. **Python version**:
   ```yaml
   python-version: '3.11'  # Update as needed
   ```

4. **Environment name** (must match PyPI Trusted Publisher):
   ```yaml
   environment: pypi  # Must match PyPI configuration
   ```

### 2.3 Create VERSION File

Create the VERSION file for local development:

```bash
mkdir -p src/<your-package-name>
echo '__version__ = "0.0.0.dev0"' > src/<your-package-name>/VERSION
```

Add to `.gitignore`:

```
# Version file (generated during build/release)
src/<your-package-name>/VERSION
```

### 2.4 Update Package Code (Optional)

If you want version access in code:

**`src/<your-package>/__about__.py`:**
```python
try:
    from importlib.metadata import version as get_package_version
except ImportError:
    from importlib_metadata import version as get_package_version

try:
    __version__ = get_package_version("your-package-name")
except Exception:
    import os
    from pathlib import Path

    version_file = Path(__file__).parent / "VERSION"
    if version_file.exists():
        __version__ = version_file.read_text().strip().split('"')[1]
    else:
        __version__ = os.environ.get("HATCH_CALVER_VERSION", "0.0.0.dev0")
```

**`src/<your-package>/__init__.py`:**
```python
from <your-package>.__about__ import __version__

__all__ = ["__version__"]
```

---

## Step 3: Configure PyPI Trusted Publishing

### 3.1 Create Trusted Publisher on PyPI

1. Go to your project on PyPI: `https://pypi.org/manage/projects/<project-name>`

2. Navigate to: **Manage** → **Publishing** → **Trusted Publishers**

3. Click **Add** → Select **GitHub Actions**

4. Configure:
   - **PyPI project name**: Your package name (must match exactly)
   - **Owner**: Your GitHub username/org
   - **Repository name**: Your GitHub repository name
   - **Workflow filename**: `release.yml` (must match your workflow file)
   - **Environment name**: `pypi` (must match workflow's `environment`)

5. Click **Add**

**Important:** The workflow must exist on the default branch for PyPI to verify it.

### 3.2 Verify Workflow Configuration

Ensure your `release.yml` has:

```yaml
jobs:
  release:
    environment: pypi  # Must match PyPI configuration
    permissions:
      id-token: write  # Required for Trusted Publishing
```

---

## Step 4: Test Locally

### 4.1 Test Version Calculation

```bash
# Calculate next version (should show YYYY.MM.DD.MICRO)
python scripts/calc_version.py

# With validation
python scripts/calc_version.py --validate --pep440
```

### 4.2 Generate Dev Version

```bash
# If using Makefile
make version-dev

# Or manually
VERSION=$(python scripts/calc_version.py)
echo "__version__ = \"${VERSION}.dev$(date +%s)\"" > src/<your-package>/VERSION
```

### 4.3 Test Installation

```bash
# Install in development mode
pip install -e .

# Verify version
python -c "from <your-package> import __version__; print(__version__)"
```

### 4.4 Test Build

```bash
# Build package
hatch build

# Check package
twine check dist/*
```

---

## Step 5: Test Workflow Triggers

### 5.1 Test Auto-tag Workflow

1. Create a test branch and make a small change
2. Open a pull request
3. Merge the PR to `main`/`master`
4. Check Actions tab — `auto-tag.yml` should:
   - Calculate next version
   - Create and push tag `vYYYY.MM.DD.MICRO`

### 5.2 Test Release Workflow

After `auto-tag.yml` completes, `release.yml` should:
- Trigger automatically (via `workflow_run`)
- Extract version from tag
- Build package
- Publish to PyPI

### 5.3 Manual Tag Test (Alternative)

```bash
# Create test tag
git tag v2024.01.18.99 -m "Test release"
git push origin v2024.01.18.99

# This should trigger release.yml directly (via push: tags trigger)
```

---

## Step 6: Verify PyPI Publishing

### 6.1 Check PyPI

1. Go to: `https://pypi.org/project/<your-package-name>/`
2. Verify new version appears
3. Check version matches git tag

### 6.2 Test Installation from PyPI

```bash
pip install <your-package-name>
python -c "import <your-package>; print(<your-package>.__version__)"
```

---

## Project Structure Reference

After setup, your project should have:

```
your-project/
├── .github/
│   └── workflows/
│       ├── auto-tag.yml          # Creates tags on PR merge
│       └── release.yml           # Builds and publishes to PyPI
├── scripts/
│   └── calc_version.py           # Version calculation script
├── src/
│   └── <your-package>/
│       ├── __init__.py
│       ├── __about__.py          # Optional: version metadata
│       └── VERSION               # Generated (gitignored)
├── pyproject.toml                # Updated with dynamic versioning
├── .gitignore                    # Includes VERSION file
└── Makefile                      # Optional: convenience targets
```

---

## Customization Options

### Different Package Structure

If your package is not in `src/`:

```toml
[tool.hatch.version]
path = "<your-package>/VERSION"  # Adjust path
```

Update workflow:
```yaml
echo "__version__ = \"...\"" > <your-package>/VERSION
```

### Different Version Format

To modify CalVer format, edit `scripts/calc_version.py`:
- Change date format (currently `YYYY.MM.DD`)
- Change MICRO increment logic
- Add pre-release identifiers

### Different Branch Names

Update both workflows:
```yaml
branches:
  - main
  - master
  - develop  # Add your branches
```

### Custom Environment Name

If using different environment in PyPI:
```yaml
# release.yml
environment: production  # Match PyPI config

# PyPI Trusted Publisher
Environment name: production  # Must match
```

---

## Troubleshooting

### Version Calculation Fails

**Issue:** `calc_version.py` can't find git tags
- **Fix:** Ensure you're in a git repository with tags
- **Fix:** Run `git fetch --tags` to sync remote tags

### Workflow Doesn't Trigger

**Issue:** `auto-tag.yml` doesn't run on PR merge
- **Fix:** Check branch names match your default branch
- **Fix:** Ensure workflow file exists on default branch
- **Fix:** Verify PR was merged (not just closed)

**Issue:** `release.yml` doesn't trigger after tag creation
- **Fix:** Check `workflow_run` workflow name matches `auto-tag.yml` name
- **Fix:** Verify both workflows are on default branch
- **Fix:** Check `auto-tag.yml` completed successfully

### PyPI Publishing Fails

**Issue:** `invalid-publisher` error
- **Fix:** Verify PyPI Trusted Publisher configuration matches:
  - Repository owner/name
  - Workflow filename
  - Environment name (if used)
- **Fix:** Ensure workflow has `environment: pypi` (if configured)
- **Fix:** Check publisher is "Active" not "Pending" (should activate after first publish)

**Issue:** Version file format error
- **Fix:** Ensure VERSION file contains: `__version__ = "YYYY.MM.DD.MICRO"`
- **Fix:** Check file path matches `pyproject.toml` configuration

### Local Installation Fails

**Issue:** `VERSION file does not exist`
- **Fix:** Run `make version-dev` or manually create VERSION file
- **Fix:** Ensure path in `pyproject.toml` matches actual file location

---

## Key Differences from hatch-calvar-sample-gitlab

When adapting to your project, remember to change:

1. **Package name**: Replace `hatch_calvar_sample` with your package name
2. **Project name**: Replace `hatch-calvar-sample-gitlab` with your project name
3. **GitHub owner/repo**: Update repository references
4. **Python version**: Update if using different Python version
5. **Branch names**: Adjust to match your branch naming
6. **Path structure**: Update if using different directory structure

---

## Migration Checklist

Use this checklist when migrating:

- [ ] Copied `scripts/calc_version.py`
- [ ] Copied `.github/workflows/auto-tag.yml`
- [ ] Copied `.github/workflows/release.yml`
- [ ] Updated `pyproject.toml` with dynamic versioning
- [ ] Updated workflow files with correct paths/names
- [ ] Created `VERSION` file structure
- [ ] Added `VERSION` to `.gitignore`
- [ ] Configured PyPI Trusted Publisher
- [ ] Tested version calculation locally
- [ ] Tested `version-dev` target (if using Makefile)
- [ ] Tested local installation
- [ ] Tested PR merge → tag creation
- [ ] Verified release workflow triggers
- [ ] Confirmed PyPI publishing works
- [ ] Updated project documentation

---

## Additional Resources

- **Hatch Documentation**: https://hatch.pypa.io/
- **CalVer Specification**: https://calver.org/
- **PyPI Trusted Publishers**: https://docs.pypi.org/trusted-publishers/
- **GitHub Actions**: https://docs.github.com/en/actions

---

## Example: Minimal Migration

For a minimal setup, you only need:

1. **`scripts/calc_version.py`** - Version calculation
2. **`.github/workflows/auto-tag.yml`** - Auto tag creation
3. **`.github/workflows/release.yml`** - PyPI publishing
4. **`pyproject.toml`** - Dynamic versioning config
5. **`src/<package>/VERSION`** - Version file (gitignored)

Everything else is optional but recommended for better developer experience.

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review GitHub Actions logs for specific errors
3. Verify PyPI Trusted Publisher configuration
4. Compare your setup with `hatch-calvar-sample-gitlab` reference implementation

Good luck with your CalVer migration! 🎉
