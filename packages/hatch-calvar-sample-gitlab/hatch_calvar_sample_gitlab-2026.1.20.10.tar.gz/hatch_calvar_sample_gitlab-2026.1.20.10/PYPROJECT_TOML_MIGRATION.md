# pyproject.toml Migration Guide for CalVer

This guide shows exactly what needs to be updated in `pyproject.toml` when migrating CalVer to a new project.

## CalVer-Specific Changes (Required)

These are the **only** changes needed for CalVer to work:

### 1. Add `dynamic = ["version"]` to `[project]` section

**Current (hatch-calvar-sample-gitlab):**
```toml
[project]
name = "hatch-calvar-sample-gitlab"
dynamic = ["version"]  # ← ADD THIS
description = "..."
```

**For your project:**
```toml
[project]
name = "your-package-name"
dynamic = ["version"]  # ← REQUIRED for CalVer
description = "..."
```

### 2. Add `[tool.hatch.version]` section

**Current (hatch-calvar-sample-gitlab):**
```toml
[tool.hatch.version]
path = "src/hatch_calvar_sample/VERSION"
```

**For your project:**
```toml
[tool.hatch.version]
path = "src/<your-package-name>/VERSION"  # ← Update path to your package location
```

**Note:** If your package is not in `src/` directory:
```toml
[tool.hatch.version]
path = "<your-package-name>/VERSION"  # Direct package location
```

---

## Project-Specific Changes (Update for your project)

These need to be customized for your project:

### 1. Package Name

**Change:**
```toml
[project]
name = "hatch-calvar-sample-gitlab"  # ← Change to your package name
```

**To:**
```toml
[project]
name = "your-package-name"  # PyPI package name (use hyphens)
```

### 2. Description

**Change:**
```toml
description = 'Sample project demonstrating CalVer (YYYY.MM.DD.MICRO) with hatch'
```

**To:**
```toml
description = "Your project description"
```

### 3. Author Information

**Change:**
```toml
authors = [
  { name = "QAToolist", email = "qatoolist@gmail.com" },
]
```

**To:**
```toml
authors = [
  { name = "Your Name", email = "your.email@example.com" },
]
```

### 4. Project URLs

**Change:**
```toml
[project.urls]
Documentation = "https://gitlab.com/QAToolist/hatch-calvar-sample-gitlab#readme"
Issues = "https://gitlab.com/QAToolist/hatch-calvar-sample-gitlab/-/issues"
Source = "https://gitlab.com/QAToolist/hatch-calvar-sample-gitlab"
```

**To:**
```toml
[project.urls]
Documentation = "https://gitlab.com/<your-username>/<your-repo>#readme"
Issues = "https://gitlab.com/<your-username>/<your-repo>/-/issues"
Source = "https://gitlab.com/<your-username>/<your-repo>"
```

### 5. CLI Scripts (if applicable)

**Current (hatch-calvar-sample-gitlab):**
```toml
[project.scripts]
calver-check = "hatch_calvar_sample.cli:main"
```

**For your project:**
```toml
# If you have CLI scripts:
[project.scripts]
your-command = "your_package.cli:main"

# If you don't have CLI scripts, remove this section
```

### 6. Path References in Tool Configurations

**Current (hatch-calvar-sample-gitlab):**
```toml
[tool.hatch.envs.types.scripts]
check = "mypy --install-types --non-interactive {args:src/hatch_calvar_sample tests}"

[tool.coverage.run]
source_pkgs = ["hatch_calvar_sample", "tests"]

[tool.coverage.paths]
hatch_calvar_sample = ["src/hatch_calvar_sample", "*/hatch-calvar-sample-gitlab/src/hatch_calvar_sample"]
```

**For your project:**
```toml
[tool.hatch.envs.types.scripts]
check = "mypy --install-types --non-interactive {args:src/<your-package-name> tests}"

[tool.coverage.run]
source_pkgs = ["<your-package-name>", "tests"]

[tool.coverage.paths]
<your-package-name> = ["src/<your-package-name>", "*/<your-package-name>/src/<your-package-name>"]
```

**Note:** Replace `hatch_calvar_sample` with your package name in all tool configurations.

---

## Complete Example: Before and After

### Before (hatch-calvar-sample-gitlab)

```toml
[project]
name = "hatch-calvar-sample-gitlab"
# ... other fields ...
dynamic = ["version"]

[tool.hatch.version]
path = "src/hatch_calvar_sample/VERSION"
```

### After (your project)

```toml
[project]
name = "your-package-name"
# ... other fields ...
dynamic = ["version"]  # ← ADDED for CalVer

[tool.hatch.version]
path = "src/your_package_name/VERSION"  # ← Updated path
```

---

## Minimal Required Changes Summary

For CalVer to work, you **must** add/update:

1. ✅ **`dynamic = ["version"]`** in `[project]` section
2. ✅ **`[tool.hatch.version]`** section with correct path

**Everything else is optional** and depends on your project needs.

---

## Quick Migration Checklist

- [ ] Add `dynamic = ["version"]` to `[project]` section
- [ ] Add `[tool.hatch.version]` section with path to your VERSION file
- [ ] Update `name` to your package name
- [ ] Update `description` to your project description
- [ ] Update `authors` to your information
- [ ] Update `[project.urls]` to your repository URLs
- [ ] Remove or update `[project.scripts]` (if not using CLI)
- [ ] Update package name references in `[tool.hatch.envs]` (if present)
- [ ] Update package name references in `[tool.coverage]` (if present)

---

## Important Notes

### Path Format in `[tool.hatch.version]`

The path must:
- Point to the actual VERSION file location
- Use forward slashes `/` (even on Windows)
- Be relative to the project root
- Match the path where VERSION file will be created/generated

**Examples:**
```toml
# Package in src/ directory
[tool.hatch.version]
path = "src/my_package/VERSION"

# Package in root directory
[tool.hatch.version]
path = "my_package/VERSION"

# Package in different location
[tool.hatch.version]
path = "packages/core/VERSION"
```

### VERSION File Format

The VERSION file must contain:
```
__version__ = "YYYY.MM.DD.MICRO"
```

This is automatically generated by workflows and `make version-dev`, but must match this format.

### No Other Changes Needed for CalVer

You **don't need** to change:
- Build system configuration (`[build-system]`)
- Python version requirements (`requires-python`)
- Dependencies (`dependencies`)
- License format
- Any other tool configurations (unless they reference package names)

---

## Testing Your Configuration

After updating `pyproject.toml`:

1. **Verify VERSION path exists:**
   ```bash
   ls -la src/<your-package>/VERSION  # Should exist or be created
   ```

2. **Test version reading:**
   ```bash
   python -c "import tomli; print(tomli.load(open('pyproject.toml'))['tool']['hatch']['version'])"
   ```

3. **Test build:**
   ```bash
   hatch build  # Should succeed with VERSION file present
   ```

4. **Test installation:**
   ```bash
   pip install -e .  # Should install with version from VERSION file
   ```

---

## Common Mistakes

❌ **Missing `dynamic = ["version"]`**
- **Error:** Hatch will look for version in `pyproject.toml` directly
- **Fix:** Add `dynamic = ["version"]` to `[project]` section

❌ **Wrong VERSION file path**
- **Error:** `OSError: file does not exist: src/.../VERSION`
- **Fix:** Verify path matches actual VERSION file location

❌ **VERSION file format wrong**
- **Error:** `ValueError: unable to parse version`
- **Fix:** Ensure VERSION contains `__version__ = "YYYY.MM.DD.MICRO"`

❌ **Path uses wrong package name**
- **Error:** Build succeeds but version comes from wrong location
- **Fix:** Update all paths from `hatch_calvar_sample` to your package name

---

## Reference: Minimal pyproject.toml for CalVer

Here's a minimal example showing only CalVer requirements:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "your-package-name"
version = "0.0.0"  # Optional: default if VERSION file missing
dynamic = ["version"]  # ← REQUIRED for CalVer
description = "Your project description"
requires-python = ">=3.8"

[tool.hatch.version]
path = "src/your_package_name/VERSION"  # ← REQUIRED for CalVer
```

This minimal configuration is all you need for CalVer to work!
