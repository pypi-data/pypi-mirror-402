# hatch-calvar-sample-gitlab

[![PyPI - Version](https://img.shields.io/pypi/v/hatch-calvar-sample-gitlab.svg)](https://pypi.org/project/hatch-calvar-sample-gitlab)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-calvar-sample-gitlab.svg)](https://pypi.org/project/hatch-calvar-sample-gitlab)

Sample hatch-based Python project demonstrating **Calendar Versioning (CalVer)** with format `YYYY.MM.DD.MICRO` and automated PyPI release workflows.

## Overview

This project serves as a proof-of-concept for implementing CalVer versioning with the hatch build system. It demonstrates:

- **Calendar Versioning (YYYY.MM.DD.MICRO)** calculated from git tags
- **Dynamic versioning** with hatch build system
- **Version checking CLI tool** with multiple commands
- **Automated PyPI release** via GitLab CI/CD
- **Complete release workflow** automation

### Version Format

The project uses CalVer format: `YYYY.MM.DD.MICRO`

- `YYYY` - 4-digit year (e.g., 2024)
- `MM` - 2-digit month (01-12)
- `DD` - 2-digit day (01-31)
- `MICRO` - Sequential number for releases on the same day (1, 2, 3, ...)

Examples: `2024.01.18.1`, `2024.01.18.2`, `2024.03.15.1`

## Development Setup

### Using Dev Containers (Recommended)

This project includes a VS Code Dev Container configuration for a consistent development environment.

**Prerequisites:**
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker](https://www.docker.com/)

**Quick Start:**
1. Open the project in VS Code: `code .`
2. Press `F1` → Select: `Dev Containers: Reopen in Container`
3. Wait for container to build and dependencies to install

The container includes:
- Python 3.11 with all development tools
- Pre-commit hooks (automatically installed)
- VS Code extensions for Python development
- All project dependencies pre-installed

See [.devcontainer/README.md](.devcontainer/README.md) for detailed instructions.

### Local Installation

## Installation

```console
pip install hatch-calvar-sample-gitlab
```

## Features

### Version Calculation

The project includes a script that automatically calculates the next CalVer version based on:
- Current UTC date
- Existing git tags matching the CalVer pattern
- Automatic MICRO increment for same-day releases

### CLI Tool

The `calver-check` CLI provides multiple commands for version management:

```bash
# Calculate next version
calver-check calc

# Check current version from different sources
calver-check check

# Validate version format
calver-check validate 2024.01.18.1

# Compare two versions
calver-check compare 2024.01.18.1 2024.01.18.2

# Show version information
calver-check info
```

All commands support `--json` flag for machine-readable output:

```bash
calver-check calc --json
```

## Usage Examples

### Calculating Next Version

```bash
# Using the script directly
python scripts/calc_version.py

# Using the CLI tool
calver-check calc

# With validation
python scripts/calc_version.py --validate --pep440
```

### Checking Current Version

```bash
# Check version from package metadata
calver-check check

# Check with JSON output
calver-check check --json
```

### Validating Version Format

```bash
# Validate a version string
calver-check validate 2024.01.18.1

# Invalid version will exit with error
calver-check validate 2024.1.18.1
```

### Comparing Versions

```bash
# Compare two versions
calver-check compare 2024.01.18.1 2024.01.18.2
# Output: 2024.01.18.1 < 2024.01.18.2
```

## Release Process

### Fully Automated Release Workflow

The project uses GitLab CI/CD for **fully automated** PyPI releases. **No manual tagging required!** The workflow consists of two stages:

#### Stage 1: Auto-tag on Merge

When code is merged to `main` or `master`:

1. Automatically calculates next CalVer version using `scripts/calc_version.py`
2. Creates a git tag with format `vYYYY.MM.DD.MICRO`
3. Pushes the tag to the repository

#### Stage 2: Build and Publish

When a git tag matching `v*` is pushed:

1. Extracts version from tag (strips `v` prefix)
2. Validates CalVer format
3. Builds package with hatch
4. Validates distributions with twine
5. Publishes to PyPI using API token authentication

### Development Workflow

This project uses a **branch-based workflow** with merge requests. All changes must go through merge requests - direct pushes to `main` are not allowed.

1. **Create a feature branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit:**
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin feature/your-feature-name
   ```

3. **Create a merge request:**
   - GitLab will automatically suggest creating an MR
   - Or create manually: GitLab UI → Merge Requests → New merge request
   - Fill out the MR template checklist

4. **Wait for pipeline to pass:**
   - All required jobs must pass before merge
   - Required jobs: `pre-commit`, `lint`, `test`, `sast-bandit`, `dependency-scanning`, `secret-detection`, `code-quality`, `build-verify`

5. **Merge to main:**
   - Once approved and pipelines pass, merge the MR
   - Auto-tag job will run automatically
   - Release job will publish to PyPI

### Automated Release Steps

1. **Open a merge request** with your changes
2. **Wait for all pipeline jobs to pass** (pre-commit, lint, test, security scans, etc.)
3. **Get required approvals** (if configured)
4. **Merge the merge request** to `main`/`master`
5. **GitLab CI/CD automatically:**
   - Calculates next CalVer version (e.g., `2024.01.18.1`)
   - Creates tag `v2024.01.18.1`
   - Builds the package
   - Validates version format
   - Publishes to PyPI

No manual tagging required! The release happens automatically when merge requests are merged.

### GitLab CI/CD Pipeline

The project includes a comprehensive `.gitlab-ci.yml` with the following pipeline stages:

**Validate Stage:**
- **pre-commit**: Runs pre-commit hooks (formatting, linting, security)
- **lint**: Code quality checks (black, isort, ruff, mypy)

**Test Stage:**
- **test**: Runs tests across multiple Python versions (3.8-3.12) with coverage reporting (≥70% required)

**Security Stage:**
- **sast-bandit**: Static Application Security Testing
- **dependency-scanning**: Dependency vulnerability scanning (Safety, pip-audit)
- **secret-detection**: Secret/key detection (Gitleaks)

**Quality Stage:**
- **code-quality**: Code complexity and maintainability analysis (Radon, Xenon)

**Build Stage:**
- **build-verify**: Builds and verifies package installation across Python 3.9 and 3.11

**Compliance Stage:**
- **license-check**: Checks license compliance and generates license reports

**Release Stage:**
- **auto-tag**: Automatically creates release tags when code is merged to main/master
- **release**: Builds and publishes packages to PyPI when tags are pushed

### Merge Request Requirements

Before a merge request can be merged, the following must pass:
- ✅ All pipeline jobs (pre-commit, lint, test, security, quality, build)
- ✅ Test coverage ≥70%
- ✅ All discussions resolved
- ✅ Required approvals (if configured)

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development workflow.

To enable PyPI publishing, configure the `PYPI_API_TOKEN` variable in GitLab CI/CD settings (Settings → CI/CD → Variables).

### Manual Release (Optional)

If you need to manually create a release tag (for hotfixes, etc.):

1. **Calculate next version:**
   ```bash
   calver-check calc
   # Output: 2024.01.18.1
   ```

2. **Create and push git tag:**
   ```bash
   git tag v2024.01.18.1 -m "Release 2024.01.18.1"
   git push origin v2024.01.18.1
   ```

The tag push will trigger the same build and publish workflow.

### Using Makefile

For convenience, use the Makefile targets:

```bash
# Calculate next version
make version-calc

# Check current version
make version-check

# Validate version format
make version-validate VERSION=2024.01.18.1

# Create and push release tag
make release-tag

# Build package for testing
make build-test
```

## Project Structure

```
hatch-calvar-sample-gitlab/
├── pyproject.toml              # Hatch configuration with dynamic versioning
├── README.md                   # This file
├── CHANGELOG.md                # Changelog with CalVer format
├── LICENSE.txt                 # MIT license
├── Makefile                    # Convenient make targets
├── .gitlab-ci.yml              # GitLab CI/CD pipeline configuration
│                               # Includes: test, build-verify, license-check, auto-tag, release
├── scripts/
│   └── calc_version.py         # Version calculation script
├── src/
│   └── hatch_calvar_sample/
│       ├── __init__.py         # Package with __version__
│       ├── __about__.py        # Version metadata
│       ├── VERSION             # Version file (generated during build)
│       └── cli.py              # Version checking CLI implementation
└── tests/
    ├── test_version_calc.py    # Tests for version calculation
    └── test_version_cli.py     # Tests for CLI tool
```

## Configuration

### Dynamic Versioning

The project uses hatch's dynamic versioning feature configured in `pyproject.toml`:

```toml
[tool.hatch.version]
path = "src/hatch_calvar_sample/VERSION"
```

The VERSION file is created during the release workflow with the version extracted from the git tag.

### Version Metadata in Code

The package reads version from `importlib.metadata` when installed, with fallbacks:

1. Package metadata (when installed)
2. VERSION file (for development builds)
3. Environment variable `HATCH_CALVER_VERSION`

Access version programmatically:

```python
from hatch_calvar_sample import __version__

print(__version__)  # Output: 2024.01.18.1
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://gitlab.com/QAToolist/hatch-calvar-sample-gitlab.git
cd hatch-calvar-sample-gitlab

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_version_calc.py

# Run with coverage
pytest --cov=hatch_calvar_sample --cov=scripts
```

### Local Testing

1. **Test version calculation:**
   ```bash
   python scripts/calc_version.py
   ```

2. **Test build process:**
   ```bash
   # Create VERSION file manually
   echo "2024.01.18.1" > src/hatch_calvar_sample/VERSION

   # Build package
   hatch build

   # Check built package
   twine check dist/*
   ```

3. **Test installation:**
   ```bash
   pip install -e .
   python -c "import hatch_calvar_sample; print(hatch_calvar_sample.__version__)"
   ```

## Version Calculation Logic

The version calculation script:

1. Gets current UTC date → `YYYY.MM.DD`
2. Fetches all git tags (`git fetch --tags`)
3. Parses tags matching CalVer pattern (`YYYY.MM.DD.MICRO` or `vYYYY.MM.DD.MICRO`)
4. Filters tags with the same date
5. Extracts MICRO numbers
6. Calculates next MICRO = `max(existing) + 1` or `1` if none exist
7. Returns: `YYYY.MM.DD.MICRO`

### Edge Cases Handled

- No tags → Returns `YYYY.MM.DD.1`
- Multiple tags same date → Increments MICRO correctly
- Date boundary crossing → Resets MICRO to 1 for new date
- Invalid tag formats → Skipped gracefully
- Timezone handling → Uses UTC for consistency

## PEP 440 Compliance

CalVer format `YYYY.MM.DD.MICRO` is PEP 440 compliant as a release segment. The format:

- Uses numeric components
- Follows semantic ordering (newer dates > older dates)
- Valid for PyPI distribution

Validate PEP 440 compliance:

```bash
calver-check validate 2024.01.18.1
python scripts/calc_version.py --pep440
```

## Troubleshooting

### GitLab CI/CD Issues

For common GitLab CI/CD configuration issues, build problems, and PyPI publishing issues, see the comprehensive [GitLab CI/CD Troubleshooting Guide](GITLAB_CI_TROUBLESHOOTING.md).

Common issues covered:
- CI/CD variable configuration (Protected flags, environment scope)
- Build and package directory issues
- Tag creation and auto-tagging problems
- PyPI publishing failures
- Pipeline configuration errors

### Version Not Found

If `__version__` is not available:

1. Ensure package is installed: `pip install -e .`
2. Check VERSION file exists: `ls src/hatch_calvar_sample/VERSION`
3. Verify git tags: `git tag`

### Build Errors

If build fails:

1. Verify VERSION file exists with valid format
2. Check `pyproject.toml` dynamic version configuration
3. Ensure hatch is installed: `pip install hatchling`
4. See [GitLab CI/CD Troubleshooting Guide](GITLAB_CI_TROUBLESHOOTING.md) for package directory issues

### CLI Not Found

If `calver-check` command is not available:

1. Reinstall package: `pip install -e .`
2. Check entry point in `pyproject.toml`
3. Verify PATH includes Python scripts directory

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Development workflow (branch-based with merge requests)
- Branch naming conventions
- Commit message guidelines
- Code standards and testing requirements
- Merge request process

**Quick Start:**
1. Create a branch: `git checkout -b feature/your-feature`
2. Make changes and commit
3. Push branch and create merge request
4. Wait for pipeline to pass
5. Get approval and merge

For more details, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

`hatch-calvar-sample-gitlab` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## References

- [Hatch Documentation](https://hatch.pypa.io/)
- [Calendar Versioning (CalVer)](https://calver.org/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
