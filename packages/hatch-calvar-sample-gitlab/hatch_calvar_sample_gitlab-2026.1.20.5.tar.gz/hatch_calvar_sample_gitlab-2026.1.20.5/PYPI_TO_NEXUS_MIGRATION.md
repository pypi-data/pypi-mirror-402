# PyPI to Sonatype Nexus Migration Plan

## Overview

This document provides a comprehensive guide for migrating the automated release workflow from PyPI to Sonatype Nexus Artifact Repository. This migration maintains the same CalVer versioning and automated release process while changing the package distribution target.

## Table of Contents

- [Key Differences: PyPI vs Nexus](#key-differences-pypi-vs-nexus)
- [Prerequisites](#prerequisites)
- [Required Changes](#required-changes)
- [Step-by-Step Migration Guide](#step-by-step-migration-guide)
- [Configuration Details](#configuration-details)
- [Testing Procedures](#testing-procedures)
- [Troubleshooting](#troubleshooting)
- [Rollback Plan](#rollback-plan)

---

## Key Differences: PyPI vs Nexus

### PyPI (Current Setup)

- **Authentication:** API token only (`__token__` username)
- **Repository URL:** Fixed endpoint `https://upload.pypi.org/legacy/`
- **Access:** Public repository
- **Package Index:** Standard PyPI index
- **Installation:** `pip install package-name` (from PyPI)

### Sonatype Nexus (Target)

- **Authentication:** Username/password or API token
- **Repository URL:** Custom URL (e.g., `https://nexus.example.com/repository/pypi-releases/`)
- **Access:** Can be private/internal
- **Package Index:** Custom Nexus repository
- **Installation:** `pip install --index-url https://nexus.example.com/repository/pypi-releases/simple package-name`

### Comparison Table

| Feature | PyPI | Nexus |
|---------|------|-------|
| Authentication | API Token | Username/Password or Token |
| Repository URL | Fixed | Configurable |
| Access Control | Public | Private/Internal possible |
| Package Index | Standard | Custom |
| Installation | Direct | Requires index URL |

---

## Prerequisites

Before starting the migration, ensure you have:

1. **Nexus Repository Access:**
   - Nexus instance URL
   - Repository name/ID for Python packages
   - Valid credentials (username/password or API token)
   - Appropriate permissions to upload packages

2. **Repository Information:**
   - Repository type (hosted, proxy, or group)
   - Repository format (pypi)
   - Repository name (e.g., `pypi-releases`, `pypi-snapshots`)

3. **GitLab Access:**
   - Access to project CI/CD variables
   - Ability to modify `.gitlab-ci.yml`

4. **Testing Environment:**
   - Ability to create test tags
   - Access to verify packages in Nexus

---

## Required Changes

### 1. GitLab CI/CD Variables

#### Current Variables (PyPI)
- `PYPI_API_TOKEN` - PyPI API token

#### New Variables (Nexus)
- `NEXUS_URL` - Base URL of Nexus instance (e.g., `https://nexus.example.com`)
- `NEXUS_REPOSITORY` - Repository name/ID (e.g., `pypi-releases`)
- `NEXUS_USERNAME` - Nexus username for authentication
- `NEXUS_PASSWORD` - Nexus password (or use `NEXUS_TOKEN` if supported)

#### Optional Variables
- `NEXUS_REPOSITORY_PATH` - Full repository path (if different from standard `$NEXUS_URL/repository/$NEXUS_REPOSITORY/`)

### 2. GitLab CI/CD Configuration (.gitlab-ci.yml)

#### Current Configuration (PyPI)
```yaml
release:
  # ... other config ...
  script:
    - |
      if [ -z "$PYPI_API_TOKEN" ]; then
        echo "ERROR: PYPI_API_TOKEN not set..."
        exit 1
      fi
      twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*
```

#### New Configuration (Nexus)
```yaml
release:
  # ... other config ...
  script:
    - |
      # Validate Nexus variables
      if [ -z "$NEXUS_URL" ] || [ -z "$NEXUS_REPOSITORY" ] || [ -z "$NEXUS_USERNAME" ] || [ -z "$NEXUS_PASSWORD" ]; then
        echo "ERROR: Nexus variables not configured..."
        exit 1
      fi

      # Construct repository URL
      NEXUS_REPO_URL="${NEXUS_URL}/repository/${NEXUS_REPOSITORY}/"

      # Upload to Nexus
      twine upload --repository-url "$NEXUS_REPO_URL" \
                   --username "$NEXUS_USERNAME" \
                   --password "$NEXUS_PASSWORD" \
                   dist/*
```

### 3. Environment Configuration

**Current:**
```yaml
environment:
  name: pypi
```

**New (Optional - for clarity):**
```yaml
environment:
  name: nexus
```

### 4. Documentation Updates

Files requiring updates:
- `README.md` - Update release workflow description
- `GITLAB_CI_TROUBLESHOOTING.md` - Add Nexus-specific troubleshooting
- `CALVER_MIGRATION_GUIDE.md` - Add Nexus publishing option (optional)

---

## Step-by-Step Migration Guide

### Step 1: Gather Nexus Information

1. **Identify Nexus Instance:**
   - Base URL: `https://nexus.example.com`
   - Verify accessibility from GitLab runners

2. **Identify Repository:**
   - Repository name: `pypi-releases` (or your custom name)
   - Repository type: Should be "hosted" for uploads
   - Repository format: Should be "pypi"

3. **Get Credentials:**
   - Username: `nexus-user` (or service account)
   - Password: `nexus-password` (or API token if supported)

4. **Verify Repository URL:**
   - Full URL format: `https://nexus.example.com/repository/pypi-releases/`
   - Test URL accessibility

### Step 2: Configure GitLab CI/CD Variables

1. **Go to GitLab Project Settings:**
   - Navigate to: Settings → CI/CD → Variables

2. **Add Nexus Variables:**

   **NEXUS_URL:**
   - Key: `NEXUS_URL`
   - Value: `https://nexus.example.com` (your Nexus base URL)
   - Type: Variable
   - Environment scope: (leave blank)
   - Flags:
     - ❌ Masked: No (URL is not sensitive)
     - ❌ Protected: No (unless tags are protected)
     - ❌ Expand variable reference: No

   **NEXUS_REPOSITORY:**
   - Key: `NEXUS_REPOSITORY`
   - Value: `pypi-releases` (your repository name)
   - Type: Variable
   - Environment scope: (leave blank)
   - Flags:
     - ❌ Masked: No (repository name is not sensitive)
     - ❌ Protected: No (unless tags are protected)
     - ❌ Expand variable reference: No

   **NEXUS_USERNAME:**
   - Key: `NEXUS_USERNAME`
   - Value: `your-nexus-username`
   - Type: Variable
   - Environment scope: (leave blank)
   - Flags:
     - ✅ Masked: Yes (recommended)
     - ❌ Protected: No (unless tags are protected)
     - ❌ Expand variable reference: No

   **NEXUS_PASSWORD:**
   - Key: `NEXUS_PASSWORD`
   - Value: `your-nexus-password`
   - Type: Variable
   - Environment scope: (leave blank)
   - Flags:
     - ✅ Masked: Yes (required - sensitive data)
     - ❌ Protected: No (unless tags are protected)
     - ❌ Expand variable reference: No

3. **Remove or Keep PyPI Variable:**
   - Option A: Remove `PYPI_API_TOKEN` (if fully migrating)
   - Option B: Keep it (if supporting both PyPI and Nexus)

### Step 3: Update .gitlab-ci.yml

1. **Locate the `release` job** in `.gitlab-ci.yml`

2. **Replace PyPI authentication check:**
   ```yaml
   # OLD (PyPI)
   if [ -z "$PYPI_API_TOKEN" ]; then
     echo "ERROR: PYPI_API_TOKEN not set..."
   fi

   # NEW (Nexus)
   if [ -z "$NEXUS_URL" ] || [ -z "$NEXUS_REPOSITORY" ] || \
      [ -z "$NEXUS_USERNAME" ] || [ -z "$NEXUS_PASSWORD" ]; then
     echo "ERROR: Nexus variables not configured..."
     echo "Required variables: NEXUS_URL, NEXUS_REPOSITORY, NEXUS_USERNAME, NEXUS_PASSWORD"
     exit 1
   fi
   ```

3. **Update repository URL construction:**
   ```yaml
   # Construct Nexus repository URL
   NEXUS_REPO_URL="${NEXUS_URL}/repository/${NEXUS_REPOSITORY}/"

   # Remove trailing slash if present in base URL
   NEXUS_REPO_URL="${NEXUS_REPO_URL//\/\//\/}"
   ```

4. **Replace twine upload command:**
   ```yaml
   # OLD (PyPI)
   twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*

   # NEW (Nexus)
   twine upload --repository-url "$NEXUS_REPO_URL" \
                --username "$NEXUS_USERNAME" \
                --password "$NEXUS_PASSWORD" \
                dist/*
   ```

5. **Update success message:**
   ```yaml
   # OLD
   echo "✓ Successfully published to PyPI: https://pypi.org/project/hatch-calvar-sample-gitlab/"

   # NEW
   echo "✓ Successfully published to Nexus: ${NEXUS_REPO_URL}"
   ```

6. **Update environment name (optional):**
   ```yaml
   environment:
     name: nexus  # Changed from 'pypi'
   ```

### Step 4: Update Documentation

#### Update README.md

1. **Update release workflow description:**
   ```markdown
   # OLD
   - Publishes to PyPI using Trusted Publishing

   # NEW
   - Publishes to Sonatype Nexus Artifact Repository
   ```

2. **Update installation instructions (if packages are in Nexus):**
   ```markdown
   ## Installation from Nexus

   ```bash
   pip install --index-url https://nexus.example.com/repository/pypi-releases/simple hatch-calvar-sample-gitlab
   ```
   ```

#### Update GITLAB_CI_TROUBLESHOOTING.md

Add new section:
```markdown
## Nexus Publishing Issues

### Issue: Release Job Fails with Authentication Error

**Symptoms:**
- Job fails with "401 Unauthorized" or "403 Forbidden"
- Packages not uploaded to Nexus

**Solutions:**
1. Verify NEXUS_USERNAME and NEXUS_PASSWORD are correct
2. Check user has upload permissions in Nexus
3. Verify repository URL is correct
4. Check Nexus repository is in "hosted" mode (not proxy)
```

### Step 5: Test the Migration

1. **Create a test tag:**
   ```bash
   git tag v2026.01.20.99 -m "Test Nexus migration"
   git push origin v2026.01.20.99
   ```

2. **Monitor the pipeline:**
   - Check GitLab CI/CD → Pipelines
   - Verify release job runs
   - Check job logs for errors

3. **Verify package in Nexus:**
   - Log into Nexus web interface
   - Navigate to your repository
   - Verify package appears: `hatch-calvar-sample-gitlab-2026.01.20.99.tar.gz`
   - Verify wheel file: `hatch-calvar-sample-gitlab-2026.01.20.99-py3-none-any.whl`

4. **Test installation from Nexus:**
   ```bash
   pip install --index-url https://nexus.example.com/repository/pypi-releases/simple \
              --trusted-host nexus.example.com \
              hatch-calvar-sample-gitlab==2026.01.20.99
   ```

5. **Delete test tag:**
   ```bash
   git tag -d v2026.01.20.99
   git push origin :refs/tags/v2026.01.20.99
   ```

---

## Configuration Details

### Nexus Repository URL Format

Standard format:
```
https://nexus.example.com/repository/pypi-releases/
```

Components:
- Base URL: `https://nexus.example.com`
- Path: `/repository/`
- Repository name: `pypi-releases`
- Trailing slash: Required for twine

### Twine Upload Command

Full command structure:
```bash
twine upload \
  --repository-url "https://nexus.example.com/repository/pypi-releases/" \
  --username "nexus-user" \
  --password "nexus-password" \
  --verbose \
  dist/*
```

### Authentication Methods

#### Method 1: Username/Password (Recommended)
```yaml
NEXUS_USERNAME: your-username
NEXUS_PASSWORD: your-password
```

#### Method 2: API Token (if Nexus supports)
Some Nexus versions support API tokens:
```yaml
NEXUS_USERNAME: your-username
NEXUS_PASSWORD: api-token-value
```

### Repository Types

- **Hosted:** For uploading your own packages (use this)
- **Proxy:** For proxying external repositories (not for uploads)
- **Group:** For combining multiple repositories (not for uploads)

Ensure your repository is configured as "hosted" type.

---

## Testing Procedures

### Pre-Migration Testing

1. **Test Nexus Connectivity:**
   ```bash
   curl -u $NEXUS_USERNAME:$NEXUS_PASSWORD \
        https://nexus.example.com/repository/pypi-releases/
   ```

2. **Test Repository Access:**
   - Verify you can browse repository in Nexus UI
   - Verify upload permissions

3. **Test Local Upload:**
   ```bash
   # Build package locally
   hatch build

   # Test upload to Nexus
   twine upload --repository-url "https://nexus.example.com/repository/pypi-releases/" \
                --username "$NEXUS_USERNAME" \
                --password "$NEXUS_PASSWORD" \
                dist/*
   ```

### Post-Migration Testing

1. **Automated Pipeline Test:**
   - Create test tag
   - Monitor pipeline execution
   - Verify job succeeds
   - Check Nexus for uploaded packages

2. **Package Verification:**
   - Verify package metadata in Nexus
   - Verify both wheel and sdist are uploaded
   - Check package version matches tag

3. **Installation Test:**
   - Install from Nexus repository
   - Verify package functionality
   - Test CLI tools if applicable

---

## Troubleshooting

### Common Issues

#### Issue 1: Authentication Failure (401 Unauthorized)

**Symptoms:**
```
HTTPError: 401 Client Error: Unauthorized
```

**Solutions:**
1. Verify `NEXUS_USERNAME` and `NEXUS_PASSWORD` are correct
2. Check credentials in Nexus UI
3. Verify user has upload permissions
4. Check if password contains special characters (may need URL encoding)

#### Issue 2: Repository Not Found (404 Not Found)

**Symptoms:**
```
HTTPError: 404 Client Error: Not Found
```

**Solutions:**
1. Verify `NEXUS_REPOSITORY` name is correct
2. Check repository exists in Nexus
3. Verify repository URL format: `$NEXUS_URL/repository/$NEXUS_REPOSITORY/`
4. Check repository is "hosted" type (not proxy or group)

#### Issue 3: Permission Denied (403 Forbidden)

**Symptoms:**
```
HTTPError: 403 Client Error: Forbidden
```

**Solutions:**
1. Verify user has "write" or "deploy" permissions
2. Check repository permissions in Nexus
3. Verify repository is not read-only
4. Check user role assignments

#### Issue 4: SSL/TLS Certificate Issues

**Symptoms:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**
1. Add `--trusted-host` flag (not recommended for production)
2. Configure proper SSL certificates
3. Use `--cert` flag with certificate file
4. Verify Nexus SSL certificate is valid

#### Issue 5: Variable Not Available

**Symptoms:**
```
ERROR: Nexus variables not configured
```

**Solutions:**
1. Verify all required variables are set in GitLab CI/CD
2. Check variable names are exact (case-sensitive)
3. Verify variables are not "Protected" unless tags are protected
4. Check environment scope matches

### Debug Commands

Add to `.gitlab-ci.yml` for debugging:
```yaml
- |
  echo "Debug: Nexus Configuration"
  echo "NEXUS_URL: ${NEXUS_URL}"
  echo "NEXUS_REPOSITORY: ${NEXUS_REPOSITORY}"
  echo "NEXUS_USERNAME: ${NEXUS_USERNAME}"
  echo "NEXUS_REPO_URL: ${NEXUS_REPO_URL}"
  echo "Testing connectivity..."
  curl -u "${NEXUS_USERNAME}:${NEXUS_PASSWORD}" \
       "${NEXUS_REPO_URL}" \
       -v
```

---

## Rollback Plan

If the migration needs to be reverted:

### Step 1: Restore PyPI Configuration

1. **Restore .gitlab-ci.yml:**
   - Revert changes to release job
   - Restore PyPI upload command
   - Restore PyPI variable checks

2. **Restore CI/CD Variables:**
   - Ensure `PYPI_API_TOKEN` is configured
   - Remove or disable Nexus variables (optional)

3. **Restore Environment:**
   ```yaml
   environment:
     name: pypi
   ```

### Step 2: Test Rollback

1. Create test tag
2. Verify pipeline uses PyPI
3. Verify package uploads to PyPI
4. Verify package is available on PyPI

### Step 3: Update Documentation

- Revert README.md changes
- Revert troubleshooting guide changes
- Update any migration-specific documentation

---

## Migration Checklist

### Pre-Migration
- [ ] Gather Nexus instance information
- [ ] Verify Nexus repository exists and is accessible
- [ ] Obtain Nexus credentials
- [ ] Test Nexus connectivity
- [ ] Test local upload to Nexus
- [ ] Review current PyPI configuration

### Migration
- [ ] Add Nexus CI/CD variables to GitLab
- [ ] Update `.gitlab-ci.yml` release job
- [ ] Update environment name (optional)
- [ ] Update README.md
- [ ] Update troubleshooting guide
- [ ] Commit and push changes

### Post-Migration Testing
- [ ] Create test tag
- [ ] Monitor pipeline execution
- [ ] Verify package uploads to Nexus
- [ ] Verify package appears in Nexus UI
- [ ] Test package installation from Nexus
- [ ] Verify package functionality
- [ ] Delete test tag

### Documentation
- [ ] Update README.md with Nexus installation instructions
- [ ] Update troubleshooting guide with Nexus issues
- [ ] Document Nexus repository URL for users
- [ ] Update any migration guides

---

## Additional Considerations

### Supporting Both PyPI and Nexus

If you want to support both repositories:

1. **Use conditional logic:**
   ```yaml
   - |
     if [ -n "$PYPI_API_TOKEN" ]; then
       echo "Publishing to PyPI..."
       twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/*
     fi

     if [ -n "$NEXUS_URL" ] && [ -n "$NEXUS_REPOSITORY" ]; then
       echo "Publishing to Nexus..."
       NEXUS_REPO_URL="${NEXUS_URL}/repository/${NEXUS_REPOSITORY}/"
       twine upload --repository-url "$NEXUS_REPO_URL" \
                    --username "$NEXUS_USERNAME" \
                    --password "$NEXUS_PASSWORD" \
                    dist/*
     fi
   ```

2. **Use separate jobs:**
   - `release-pypi` job for PyPI
   - `release-nexus` job for Nexus
   - Both triggered by tag push

### Repository Naming Conventions

Consider using different repositories for:
- **Releases:** `pypi-releases` (for stable versions)
- **Snapshots:** `pypi-snapshots` (for dev versions)

Update repository selection based on version:
```yaml
- |
  if [[ "$VERSION" =~ \.dev ]]; then
    NEXUS_REPOSITORY="pypi-snapshots"
  else
    NEXUS_REPOSITORY="pypi-releases"
  fi
```

### Security Best Practices

1. **Use Service Accounts:**
   - Create dedicated Nexus user for CI/CD
   - Limit permissions to upload only
   - Use API tokens instead of passwords when possible

2. **Rotate Credentials:**
   - Regularly rotate Nexus passwords
   - Update GitLab CI/CD variables accordingly

3. **Monitor Access:**
   - Review Nexus audit logs
   - Monitor failed upload attempts
   - Set up alerts for authentication failures

---

## References

- [Twine Documentation](https://twine.readthedocs.io/)
- [Nexus Repository Manager Documentation](https://help.sonatype.com/repomanager3)
- [Python Package Index (PEP 503)](https://peps.python.org/pep-0503/)
- [GitLab CI/CD Variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Version History

- **2026-01-20:** Initial migration plan created

---

*This migration plan should be reviewed and updated as needed based on your specific Nexus configuration and requirements.*
