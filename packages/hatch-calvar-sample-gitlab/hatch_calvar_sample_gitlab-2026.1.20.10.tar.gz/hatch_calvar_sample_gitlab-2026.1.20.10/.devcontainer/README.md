# Dev Container Setup

This project includes a VS Code Dev Container configuration for a consistent development environment.

## Prerequisites

- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker](https://www.docker.com/) (or Docker Desktop)

## Getting Started

1. **Open the project in VS Code:**
   ```bash
   code .
   ```

2. **Open Command Palette:**
   - Press `F1` or `Cmd+Shift+P` (Mac) / `Ctrl+Shift+P` (Windows/Linux)

3. **Select:**
   ```
   Dev Containers: Reopen in Container
   ```

4. **Wait for container to build:**
   - VS Code will build the container
   - Install Python dependencies
   - Set up pre-commit hooks
   - Configure VS Code extensions

## What's Included

### Base Image
- Python 3.11 (from Microsoft Dev Containers)
- Git
- GitHub CLI

### Pre-installed Tools
- All project dependencies (`pip install -e '.[dev]'`)
- Pre-commit hooks (automatically installed)
- Development tools:
  - black, isort, ruff (formatting/linting)
  - mypy (type checking)
  - pytest (testing)
  - bandit (security scanning)
  - radon, xenon (code quality)
  - safety, pip-audit (dependency scanning)

### VS Code Extensions
- Python extension with Pylance
- Black formatter
- isort
- Ruff
- MyPy type checker
- Pytest
- GitLens
- YAML support
- TOML support

## Usage

Once the container is running:

1. **Run tests:**
   ```bash
   pytest
   ```

2. **Format code:**
   ```bash
   black src/ tests/
   isort src/ tests/
   ```

3. **Lint code:**
   ```bash
   ruff check src/ tests/
   mypy src/
   ```

4. **Run pre-commit:**
   ```bash
   pre-commit run --all-files
   ```

5. **Build package:**
   ```bash
   hatch build
   ```

## Customization

Edit `.devcontainer/devcontainer.json` to:
- Change Python version
- Add additional VS Code extensions
- Modify post-create commands
- Add environment variables
- Configure port forwarding

## Troubleshooting

### Container won't start
- Ensure Docker is running
- Check Docker Desktop is started (if using Docker Desktop)

### Dependencies not installing
- Check internet connection
- Review container logs: `View → Output → Dev Containers`

### Pre-commit hooks not working
- Run manually: `pre-commit install`
- Check `.pre-commit-config.yaml` is present

## Rebuilding Container

If you modify `.devcontainer/devcontainer.json`:

1. Open Command Palette (`F1`)
2. Select: `Dev Containers: Rebuild Container`

## Resources

- [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Python Dev Container Guide](https://code.visualstudio.com/docs/devcontainers/containers#_python)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
