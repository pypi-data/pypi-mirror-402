# Contributing Guide

Thank you for your interest in contributing to this project! This guide outlines the development workflow and standards for contributing.

## Table of Contents

- [Development Workflow](#development-workflow)
- [Branch Naming Conventions](#branch-naming-conventions)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Merge Request Process](#merge-request-process)
- [Pipeline Requirements](#pipeline-requirements)

---

## Development Workflow

### Step 1: Start from Main

Always start your work from an up-to-date `main` branch:

```bash
git checkout main
git pull origin main
```

### Step 2: Create a Feature Branch

Create a new branch following the naming convention:

```bash
git checkout -b feature/add-new-feature
# or
git checkout -b fix/resolve-bug-description
# or
git checkout -b docs/update-readme
```

**Branch naming format:** `<type>/<description>` (maximum 80 characters)

### Step 3: Make Your Changes

1. Make your code changes
2. Run pre-commit hooks locally:
   ```bash
   pre-commit run --all-files
   ```
3. Run tests locally:
   ```bash
   pytest
   # or
   make test
   ```
4. Ensure code quality:
   ```bash
   make lint
   make security
   ```

### Step 4: Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: description of changes"
```

### Step 5: Push Your Branch

```bash
git push origin feature/add-new-feature
```

### Step 6: Create Merge Request

1. GitLab will automatically suggest creating an MR
2. Or create manually: GitLab UI → Merge Requests → New merge request
3. Fill out the MR template checklist
4. Wait for pipeline to pass
5. Address any review comments
6. Merge when approved

---

## Branch Naming Conventions

### Format

```
<type>/<description>
```

### Types

- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `chore/` - Maintenance tasks
- `perf/` - Performance improvements
- `ci/` - CI/CD changes

### Examples

✅ **Good:**
- `feature/add-user-authentication`
- `fix/resolve-memory-leak-in-cache`
- `docs/update-api-documentation`
- `refactor/simplify-version-calculation`
- `test/add-integration-tests`

❌ **Bad:**
- `my-changes` (missing type prefix)
- `fix/bug` (too vague)
- `feature/this-is-a-very-long-branch-name-that-exceeds-eighty-characters-and-should-be-shortened` (too long)
- `FEATURE/add-thing` (wrong case)

### Rules

- Maximum 80 characters total
- Use lowercase
- Use hyphens to separate words
- Be descriptive but concise
- Start with type prefix

---

## Commit Message Guidelines

### Format

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### Examples

✅ **Good:**
```
feat: add user authentication endpoint

Implements JWT-based authentication with refresh tokens.
Adds tests for authentication flow.

Closes #123
```

```
fix: resolve memory leak in cache implementation

The cache was not properly releasing references, causing
memory to accumulate over time.

Fixes #456
```

❌ **Bad:**
```
update code
```

```
fix bug
```

```
WIP: adding stuff
```

---

## Code Standards

### Pre-Commit Hooks

The project uses pre-commit hooks to enforce code quality. Install and run:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Hooks include:
- Trailing whitespace removal
- End of file fixes
- YAML/JSON/TOML validation
- Black formatting
- isort import sorting
- Ruff linting
- MyPy type checking
- Bandit security scanning

### Code Formatting

- **Black**: Code formatting (line length: 88)
- **isort**: Import sorting (profile: black)
- **Ruff**: Fast linting and formatting

Run formatting:
```bash
black src/ tests/
isort src/ tests/
ruff check --fix src/ tests/
```

### Type Checking

- **MyPy**: Static type checking
- Type hints encouraged but not required everywhere
- Use `# type: ignore` sparingly with justification

### Linting

Run linting:
```bash
make lint
# or
ruff check src/ tests/
mypy src/
```

---

## Testing Requirements

### Test Coverage

- **Minimum coverage: 70%** (enforced in CI/CD)
- Aim for higher coverage for critical code paths
- All new features must include tests
- Bug fixes must include regression tests

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/hatch_calvar_sample --cov=scripts

# Run specific test file
pytest tests/test_version_calc.py

# Run with verbose output
pytest -v
```

### Test Structure

- Tests in `tests/` directory
- Test files: `test_*.py`
- Test functions: `test_*`
- Use fixtures for common setup

### Example Test

```python
def test_calculate_next_version():
    """Test version calculation logic."""
    result = calculate_next_version()
    assert result.startswith("202")
    assert len(result.split(".")) == 4
```

---

## Merge Request Process

### Before Creating MR

- [ ] Code follows style guidelines
- [ ] Pre-commit hooks pass locally
- [ ] All tests pass locally
- [ ] Test coverage maintained or improved
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No secrets or credentials committed
- [ ] Branch name follows convention

### MR Template Checklist

When creating an MR, complete the template checklist:

- [ ] Type of change selected
- [ ] Tests added/updated
- [ ] Security review completed
- [ ] Code style verified
- [ ] Documentation updated
- [ ] License compliance verified

### MR Review Process

1. **Pipeline Runs:**
   - All jobs must pass
   - Required jobs: pre-commit, lint, test, security scans, code-quality, build-verify

2. **Code Review:**
   - At least one approval required
   - Address all review comments
   - Resolve all discussions

3. **Merge:**
   - Merge when all requirements met
   - Auto-tag will run after merge
   - Release will publish to PyPI

### Blocking Conditions

MR cannot be merged if:
- ❌ Pipeline failures in required jobs
- ❌ Test coverage below 70%
- ❌ Security vulnerabilities detected
- ❌ Missing approvals
- ❌ Unresolved discussions
- ❌ Merge conflicts

---

## Pipeline Requirements

### Required Jobs (Must Pass)

1. **pre-commit** - Pre-commit hooks
2. **lint** - Code linting and formatting
3. **test** - Unit tests (all Python versions)
4. **sast-bandit** - Security scanning
5. **dependency-scanning** - Dependency vulnerability scanning
6. **secret-detection** - Secret detection
7. **code-quality** - Code quality analysis
8. **build-verify** - Build verification

### Optional Jobs (Can Fail)

- **license-check** - License compliance (warnings allowed)

### Pipeline Stages

1. **validate** - Quick validation (pre-commit, lint)
2. **test** - Unit and integration tests
3. **security** - Security scanning
4. **quality** - Code quality analysis
5. **build** - Build verification
6. **compliance** - Compliance checks
7. **release** - Tagging and publishing (main only)

---

## Local Development Setup

### Prerequisites

- Python 3.8+
- Git
- Pre-commit hooks

### Setup Steps

1. **Clone repository:**
   ```bash
   git clone https://gitlab.com/QAToolist/hatch-calvar-sample-gitlab.git
   cd hatch-calvar-sample-gitlab
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

4. **Run tests:**
   ```bash
   pytest
   ```

### Useful Commands

```bash
# Run all checks
make check-all

# Run enterprise checks
make check-enterprise

# Run specific checks
make lint
make test
make security
make type-check
make complexity
```

---

## Getting Help

- **Documentation:** See [README.md](README.md)
- **Issues:** Create an issue in GitLab
- **Discussions:** Use GitLab discussions
- **Troubleshooting:** See [GITLAB_CI_TROUBLESHOOTING.md](GITLAB_CI_TROUBLESHOOTING.md)

---

## Code of Conduct

- Be respectful and professional
- Provide constructive feedback
- Follow project standards
- Help others learn and grow

---

*Thank you for contributing!*
