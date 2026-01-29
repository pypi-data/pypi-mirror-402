# GitLab CI/CD Troubleshooting Guide

This guide documents common issues encountered when setting up GitLab CI/CD for automated CalVer releases and PyPI publishing, along with their solutions.

## Table of Contents

- [CI/CD Variable Configuration Issues](#cicd-variable-configuration-issues)
- [Build and Package Issues](#build-and-package-issues)
- [Tag Creation Issues](#tag-creation-issues)
- [PyPI Publishing Issues](#pypi-publishing-issues)
- [Pipeline Configuration Issues](#pipeline-configuration-issues)

---

## CI/CD Variable Configuration Issues

### Issue: Variable Not Available in Pipeline

**Symptoms:**
- Job fails with "variable not set" error
- Variable exists in CI/CD settings but job can't access it
- Debug output shows variable length is 0

**Common Causes & Solutions:**

#### 1. Protected Variable on Unprotected Branch/Tag

**Problem:** Variable is marked as "Protected" but the branch or tag is not protected.

**Solution:**
- **Option A (Recommended):** Uncheck "Protected" flag for the variable
  - Go to Settings → CI/CD → Variables
  - Edit the variable
  - Uncheck "Protected"
  - Save

- **Option B:** Protect your tags/branches
  - Go to Settings → Repository → Protected Tags
  - Add pattern: `v*` (for release tags)
  - Select "Allowed to create" → Maintainers
  - Go to Settings → Repository → Protected Branches
  - Protect `main` and `master` branches

#### 2. Environment Scope Mismatch

**Problem:** Variable has an environment scope that doesn't match the job's environment.

**Solution:**
- Leave "Environment scope" blank (for all environments), OR
- Set environment scope to match the job's environment name (e.g., `pypi`)

#### 3. Case-Sensitive Variable Name

**Problem:** Variable name has incorrect casing or extra spaces.

**Solution:**
- Ensure variable key is exactly `PYPI_API_TOKEN` (case-sensitive, no spaces)
- Variable names in GitLab CI/CD are case-sensitive

#### 4. Variable Not Exported to Protected Branches/Tags

**Problem:** Variable is not available because "Export variable to pipelines running on protected branches and protected tags only" is enabled, but the branch/tag isn't protected.

**Solution:**
- Either uncheck "Export variable to pipelines running on protected branches and protected tags only", OR
- Protect your tags/branches as described above

---

## Build and Package Issues

### Issue: Hatchling Cannot Find Package Directory

**Symptoms:**
```
ValueError: Unable to determine which files to ship inside the wheel
The most likely cause of this is that there is no directory that matches
the name of your project (hatch_calvar_sample_gitlab).
```

**Problem:** After renaming the project, hatchling expects a directory matching the new project name, but the package directory still has the old name.

**Solution:**
Add explicit package location in `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/hatch_calvar_sample"]
```

This tells hatchling to use the existing package directory structure instead of inferring it from the project name.

**Note:** The Python package name (with underscores) can differ from the PyPI package name (with hyphens).

---

## Tag Creation Issues

### Issue: Auto-Tag Job Fails with "403 Forbidden"

**Symptoms:**
```
remote: You are not allowed to push code to this project.
fatal: unable to access 'https://gitlab.com/...': The requested URL returned error: 403
```

**Problem:** `CI_JOB_TOKEN` doesn't have write permissions to push tags.

**Solution:**
Configure `GITLAB_TOKEN` variable with API access:

1. **Create a Personal Access Token or Project Access Token:**
   - Go to User Settings → Access Tokens (for personal token)
   - OR Project Settings → Access Tokens (for project token)
   - Create token with `api` and `write_repository` scopes

2. **Add as CI/CD Variable:**
   - Go to Settings → CI/CD → Variables
   - Add variable:
     - **Key:** `GITLAB_TOKEN`
     - **Value:** [your access token]
     - **Type:** Variable
     - **Environment scope:** (leave blank)
     - **Flags:**
       - ✅ Masked: Yes
       - ❌ Protected: No (unless tags are protected)
       - ❌ Expand variable reference: No

3. **Alternative:** Enable CI_JOB_TOKEN API access
   - Go to Settings → CI/CD → Token Access
   - Enable "Allow CI job tokens to access the API"

The auto-tag job will use the GitLab API to create tags, which is more reliable than git push.

---

## PyPI Publishing Issues

### Issue: Release Job Succeeds But Doesn't Publish to PyPI

**Symptoms:**
- Release job completes successfully
- No packages appear on PyPI
- Job logs show: "Warning: PYPI_API_TOKEN not set. Skipping PyPI publish."

**Problem:** `PYPI_API_TOKEN` variable is not configured or not accessible.

**Solution:**

1. **Create PyPI API Token:**
   - Go to https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Name: "GitLab CI/CD" (or similar)
   - Scope: Entire account (or project-specific)
   - Copy the token (you'll only see it once!)

2. **Add to GitLab CI/CD Variables:**
   - Go to Settings → CI/CD → Variables
   - Add variable:
     - **Key:** `PYPI_API_TOKEN` (exact match, case-sensitive)
     - **Value:** [your PyPI API token]
     - **Type:** Variable
     - **Environment scope:** (leave blank for all environments)
     - **Flags:**
       - ✅ Masked: Yes (recommended - hides value in logs)
       - ❌ Protected: No (unless tags are protected)
       - ❌ Expand variable reference: No

3. **Verify Variable Settings:**
   - Ensure variable is not marked as "Protected" unless tags are protected
   - Ensure environment scope matches (or leave blank)
   - Check for typos in variable name

**Note:** The release job will now fail with a clear error message if `PYPI_API_TOKEN` is not set, preventing silent failures.

---

## Pipeline Configuration Issues

### Issue: "jobs:release config key may not be used with `rules`: only"

**Symptoms:**
```
Unable to run pipeline
jobs:release config key may not be used with `rules`: only
```

**Problem:** Job uses both `only:` and `rules:` keywords, which is not allowed in GitLab CI/CD.

**Solution:**
Remove the `only:` keyword and use only `rules:`:

```yaml
# ❌ Wrong - mixing only and rules
release:
  only:
    - tags
  rules:
    - if: $CI_COMMIT_TAG =~ /^v.*$/

# ✅ Correct - use only rules
release:
  rules:
    - if: $CI_COMMIT_TAG =~ /^v.*$/
```

**Note:** `rules:` is the modern way to define job conditions in GitLab CI/CD. The `only:`/`except:` syntax is deprecated.

---

## Recommended Variable Configuration

### GITLAB_TOKEN (for auto-tagging)

```
Key: GITLAB_TOKEN
Value: [your GitLab access token]
Type: Variable
Environment scope: (leave blank)
Flags:
  ✅ Masked: Yes
  ❌ Protected: No (unless tags are protected)
  ❌ Expand variable reference: No
```

### PYPI_API_TOKEN (for PyPI publishing)

```
Key: PYPI_API_TOKEN
Value: [your PyPI API token]
Type: Variable
Environment scope: (leave blank)
Flags:
  ✅ Masked: Yes
  ❌ Protected: No (unless tags are protected)
  ❌ Expand variable reference: No
```

---

## Debugging Tips

### Check Variable Availability

Add debug output to your job script:

```bash
echo "Variable is set: $([ -n "$VARIABLE_NAME" ] && echo 'YES' || echo 'NO')"
echo "Variable length: ${#VARIABLE_NAME}"
```

### Verify Tag Protection

Check if tags are protected:
- Go to Settings → Repository → Protected Tags
- Look for pattern matching your tags (e.g., `v*`)

### Check Environment Scope

Verify variable environment scope matches job environment:
- Job environment: Check `environment:` section in `.gitlab-ci.yml`
- Variable scope: Check in Settings → CI/CD → Variables

---

## Quick Checklist for New Repository Setup

- [ ] Configure `GITLAB_TOKEN` for auto-tagging (if using auto-tag job)
- [ ] Configure `PYPI_API_TOKEN` for PyPI publishing
- [ ] Ensure variables are not "Protected" unless tags/branches are protected
- [ ] Leave environment scope blank (or match job environment)
- [ ] Verify variable names are exact (case-sensitive)
- [ ] Test pipeline with a test tag to verify configuration
- [ ] Check job logs for any variable access issues

---

## Additional Resources

- [GitLab CI/CD Variables Documentation](https://docs.gitlab.com/ee/ci/variables/)
- [GitLab Protected Tags Documentation](https://docs.gitlab.com/ee/user/project/protected_tags.html)
- [PyPI API Tokens Documentation](https://pypi.org/help/#apitoken)
- [GitLab CI/CD Best Practices](https://docs.gitlab.com/ee/ci/pipelines/pipeline_efficiency.html)

---

## Lessons Learned

1. **Protected variables require protected branches/tags** - This is the most common issue
2. **Variable names are case-sensitive** - `PYPI_API_TOKEN` ≠ `pypi_api_token`
3. **Environment scope matters** - Blank scope = all environments
4. **Use `rules:` not `only:`** - Modern GitLab CI/CD syntax
5. **Explicit package paths** - Specify package location when project name changes
6. **Fail fast** - Jobs should fail clearly when required variables are missing

---

*Last updated: 2026-01-20*
