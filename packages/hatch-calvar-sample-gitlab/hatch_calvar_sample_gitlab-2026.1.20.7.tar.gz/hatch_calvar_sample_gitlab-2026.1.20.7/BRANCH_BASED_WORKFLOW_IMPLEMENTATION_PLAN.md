# Branch-Based Workflow Implementation Plan

## Overview

This plan implements a branch-based development workflow with merge request pipelines, ensuring code quality and security checks before merging to main, followed by automated tagging and release.

## Current State vs Target State

### Current State
- Direct pushes to main branch allowed
- Auto-tag runs on push to main
- Release runs on tag push
- Limited MR pipeline checks

### Target State
- **No direct pushes to main** - all changes via merge requests
- **Comprehensive MR pipelines** - test, pre-commit, security, quality checks
- **Auto-tag on MR merge** - triggers after merge to main
- **Release on tag** - publishes to PyPI after tag creation

---

## Workflow Process

### Developer Workflow

1. **Start from main:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/add-new-feature
   # or
   git checkout -b fix/bug-description
   # or
   git checkout -b docs/update-readme
   ```
   **Branch naming convention:** `<type>/<description>` (max 80 characters)
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `docs/` - Documentation updates
   - `refactor/` - Code refactoring
   - `test/` - Test improvements

3. **Make changes:**
   ```bash
   # Make your code changes
   git add .
   git commit -m "Descriptive commit message"
   ```

4. **Push branch:**
   ```bash
   git push origin feature/add-new-feature
   ```

5. **Create Merge Request:**
   - GitLab will automatically suggest creating MR
   - Or create manually: GitLab UI → Merge Requests → New merge request
   - MR pipelines will run automatically

6. **Wait for pipeline to pass:**
   - All required jobs must pass
   - Address any failures
   - Get approvals if required

7. **Merge to main:**
   - Once approved and pipelines pass
   - Merge request → Merge
   - Auto-tag job will run automatically
   - Release job will run after tag creation

---

## Pipeline Structure

### New Pipeline Stages

```yaml
stages:
  - validate      # Quick validation checks (pre-commit, linting)
  - test          # Unit and integration tests
  - security      # Security scanning (SAST, dependency scanning, secret detection)
  - quality       # Code quality analysis
  - build         # Build verification
  - compliance    # Compliance checks (optional for MRs)
  - release       # Tagging and publishing (main branch only)
```

### Merge Request Pipeline Jobs

**Stage: validate**
- `pre-commit` - Run pre-commit hooks
- `lint` - Code linting and formatting checks

**Stage: test**
- `test` - Unit tests with coverage (all Python versions)

**Stage: security**
- `sast-bandit` - Static Application Security Testing
- `dependency-scanning` - Dependency vulnerability scanning
- `secret-detection` - Secret/key detection

**Stage: quality**
- `code-quality` - Code complexity and maintainability
- `docs-quality` - Documentation quality checks (optional)

**Stage: build**
- `build-verify` - Build and package verification

**Stage: compliance** (optional for MRs)
- `license-check` - License compliance (can be allow_failure: true for MRs)

### Main Branch Pipeline Jobs (After MR Merge)

**Stage: release**
- `auto-tag` - Automatically create release tag
- `release` - Build and publish to PyPI (triggered by tag)

---

## Implementation Details

### 1. Pre-Commit Job

**Purpose:** Run pre-commit hooks to catch issues early.

```yaml
pre-commit:
  stage: validate
  image: python:3.11
  script:
    - python -m pip install --upgrade pip
    - pip install pre-commit
    - pre-commit run --all-files
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

### 2. Enhanced Linting Job

**Purpose:** Comprehensive code quality checks.

```yaml
lint:
  stage: validate
  image: python:3.11
  script:
    - pip install black isort ruff mypy
    - |
      echo "=== Black Formatting Check ==="
      black --check --diff src/ tests/ || exit 1
    - |
      echo "=== isort Import Sorting ==="
      isort --check-only --diff src/ tests/ || exit 1
    - |
      echo "=== Ruff Linting ==="
      ruff check src/ tests/ || exit 1
    - |
      echo "=== MyPy Type Checking ==="
      mypy src/ --ignore-missing-imports || exit 1
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

### 3. Security Scanning Jobs

**SAST (Bandit):**
```yaml
sast-bandit:
  stage: security
  image: python:3.11
  script:
    - pip install bandit[sarif]
    - bandit -r src/ -f json -o bandit-report.json || true
    - bandit -r src/ -ll || exit 1
  artifacts:
    reports:
      sast: bandit-report.json
    paths:
      - bandit-report.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

**Dependency Scanning:**
```yaml
dependency-scanning:
  stage: security
  image: python:3.11
  script:
    - pip install safety pip-audit
    - pip freeze > requirements-freeze.txt
    - |
      echo "=== Safety Check ==="
      safety check --file requirements-freeze.txt --json --output safety-report.json || true
      safety check --file requirements-freeze.txt || exit 1
    - |
      echo "=== pip-audit ==="
      pip-audit --desc --format json --output pip-audit-report.json || true
      pip-audit --desc || exit 1
  artifacts:
    reports:
      dependency_scanning: safety-report.json
    paths:
      - safety-report.json
      - pip-audit-report.json
      - requirements-freeze.txt
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

**Secret Detection:**
```yaml
secret-detection:
  stage: security
  image: zricethezav/gitleaks:latest
  script:
    - gitleaks detect --source . --verbose --report-path gitleaks-report.json
  artifacts:
    reports:
      secret_detection: gitleaks-report.json
    paths:
      - gitleaks-report.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

### 4. Code Quality Job

```yaml
code-quality:
  stage: quality
  image: python:3.11
  script:
    - pip install radon xenon
    - |
      echo "=== Code Complexity Analysis ==="
      radon cc src/ -a -j -o code-complexity.json
      radon mi src/ -j -o maintainability-index.json
      xenon src/ --max-absolute C --max-modules B --max-average A || exit 1
  artifacts:
    reports:
      codequality: code-complexity.json
    paths:
      - code-complexity.json
      - maintainability-index.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

### 5. Updated Auto-Tag Job

**Changes:**
- Only run on push to main (after MR merge)
- Remove direct push detection (should only be MR merges)
- Add MR information to tag message if available

```yaml
auto-tag:
  stage: release
  image: python:3.11
  script:
    # ... existing tag creation logic ...
    # Include MR number in tag message if available
    TAG_MESSAGE="Release ${VERSION}"
    if [ -n "$CI_MERGE_REQUEST_IID" ]; then
      TAG_MESSAGE="Release ${VERSION} (merged from MR !${CI_MERGE_REQUEST_IID})"
    fi
  rules:
    - if: $CI_COMMIT_BRANCH == "main" && $CI_PIPELINE_SOURCE == "push"
    - if: $CI_COMMIT_BRANCH == "master" && $CI_PIPELINE_SOURCE == "push"
  allow_failure: false
```

### 6. Updated Test Job

**Enhancement:**
- Enforce coverage threshold on MRs
- Fail if coverage drops below threshold

```yaml
test:
  # ... existing config ...
  script:
    # ... existing test execution ...
    - |
      # Enforce coverage on MRs and main
      if [ "$CI_PIPELINE_SOURCE" == "merge_request_event" ] || \
         [ "$CI_COMMIT_REF_NAME" == "main" ] || \
         [ "$CI_COMMIT_REF_NAME" == "master" ]; then
        coverage report --fail-under=70 || exit 1
      fi
```

---

## GitLab Project Configuration

### 1. Protected Branches

**Settings → Repository → Protected Branches:**

- **Branch:** `main`
  - Allowed to merge: Maintainers, Developers
  - Allowed to push: No one (prevents direct pushes)
  - Allowed to force push: No
  - Allowed to delete: No

- **Branch:** `master` (if used)
  - Same settings as main

### 2. Merge Request Settings

**Settings → Merge Requests:**

**Merge Checks (Required):**
- ✅ Pipeline must succeed
- ✅ All discussions must be resolved
- ✅ Status checks must succeed

**Required Jobs for Merge:**
Configure in: Settings → CI/CD → Pipeline → Required jobs

Required jobs:
- ✅ `pre-commit`
- ✅ `lint`
- ✅ `test` (at least one Python version, e.g., 3.11)
- ✅ `sast-bandit`
- ✅ `dependency-scanning`
- ✅ `secret-detection`
- ✅ `code-quality`
- ✅ `build-verify`

**Approval Rules:**
- **Code Review:** Require 1 approval
- **Security Review:** Require approval from security team (if applicable)
- **Maintainer Approval:** Required for protected branches

### 3. Push Rules (Optional but Recommended)

**Settings → Repository → Push Rules:**

- ✅ Prevent committing secrets
- ✅ Reject unsigned commits (if using GPG)
- ✅ Commit message validation (require conventional commits)

### 4. Merge Request Templates

**Create:** `.gitlab/merge_request_templates/default.md`

```markdown
## Description
<!-- Describe your changes and motivation -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Updated existing tests
- [ ] Test coverage maintained or improved

## Security
- [ ] No secrets or credentials committed
- [ ] Dependencies reviewed for vulnerabilities
- [ ] Security scan passed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] License compliance verified
- [ ] Pre-commit hooks pass locally
- [ ] Branch name follows convention (`<type>/<description>`)

## Related Issues
<!-- Link related issues: Closes #123, Related to #456 -->
```

---

## Pipeline Rules Summary

### Merge Request Pipelines

**Trigger:** When MR is created or updated

**Required Jobs:**
1. `pre-commit` - Must pass
2. `lint` - Must pass
3. `test` - Must pass (all Python versions)
4. `sast-bandit` - Must pass
5. `dependency-scanning` - Must pass
6. `secret-detection` - Must pass
7. `code-quality` - Must pass
8. `build-verify` - Must pass

**Optional Jobs:**
- `license-check` - Can fail (allow_failure: true)
- `docs-quality` - Can fail (allow_failure: true)

### Main Branch Pipelines (After MR Merge)

**Trigger:** Push to main (from MR merge)

**Jobs:**
1. All MR pipeline jobs (re-run for verification)
2. `auto-tag` - Creates release tag
3. `release` - Triggered by tag push, publishes to PyPI

**Note:** Auto-tag job runs on push to main, which creates a tag, which triggers the release job.

---

## Files to Modify

### 1. .gitlab-ci.yml

**Changes Required:**
- Add new `validate` stage
- Add new `security` stage
- Add new `quality` stage
- Add `pre-commit` job
- Add `lint` job (enhanced)
- Add `sast-bandit` job
- Add `dependency-scanning` job
- Add `secret-detection` job
- Add `code-quality` job
- Update `test` job (enforce coverage)
- Update `auto-tag` job (only on main push, include MR info)
- Update all job rules to run on MRs

### 2. Create Merge Request Template

**New File:** `.gitlab/merge_request_templates/default.md`

### 3. Update Documentation

**Files to Update:**
- `README.md` - Update workflow description
- `GITLAB_CI_TROUBLESHOOTING.md` - Add MR pipeline troubleshooting
- Create `CONTRIBUTING.md` - Developer workflow guide

---

## Implementation Steps

### Phase 1: Pipeline Restructuring

1. **Update .gitlab-ci.yml:**
   - Add new stages: `validate`, `security`, `quality`
   - Reorganize existing jobs into appropriate stages
   - Update job rules to run on MRs

2. **Add Pre-Commit Job:**
   - Create `pre-commit` job in `validate` stage
   - Ensure it runs on all MRs

3. **Add Linting Job:**
   - Create/enhance `lint` job in `validate` stage
   - Include black, isort, ruff, mypy checks

### Phase 2: Security Jobs

4. **Add SAST Job:**
   - Create `sast-bandit` job
   - Configure artifact reporting

5. **Add Dependency Scanning:**
   - Create `dependency-scanning` job
   - Configure Safety and pip-audit

6. **Add Secret Detection:**
   - Create `secret-detection` job
   - Configure Gitleaks

### Phase 3: Quality Jobs

7. **Add Code Quality Job:**
   - Create `code-quality` job
   - Configure Radon and Xenon

8. **Enhance Test Job:**
   - Enforce coverage threshold
   - Update rules for MRs

### Phase 4: Configuration

9. **Configure GitLab Settings:**
   - Protect main branch (no direct pushes)
   - Configure merge request requirements
   - Set required jobs
   - Configure approval rules

10. **Create MR Template:**
    - Create `.gitlab/merge_request_templates/default.md`
    - Add comprehensive checklist

### Phase 5: Documentation

11. **Update README.md:**
    - Document new workflow
    - Update contributing guidelines

12. **Create CONTRIBUTING.md:**
    - Step-by-step developer workflow
    - Branch naming conventions
    - Commit message guidelines

13. **Update Troubleshooting Guide:**
    - Add MR pipeline troubleshooting
    - Document common MR pipeline failures

### Phase 6: Testing

14. **Test the Workflow:**
    - Create test branch
    - Make test changes
    - Create MR
    - Verify all jobs run
    - Merge MR
    - Verify auto-tag runs
    - Verify release runs

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
- `feature/add-user-authentication`
- `fix/resolve-memory-leak-in-cache`
- `docs/update-api-documentation`
- `refactor/simplify-version-calculation`
- `test/add-integration-tests`

### Rules
- Maximum 80 characters total
- Use lowercase
- Use hyphens to separate words
- Be descriptive but concise

---

## Merge Request Requirements

### Required for Merge

1. **Pipeline Status:**
   - All required jobs must pass
   - No failed jobs (optional jobs can fail)

2. **Approvals:**
   - At least 1 code review approval
   - Security team approval (if security changes)
   - Maintainer approval (for protected branches)

3. **Discussions:**
   - All discussions must be resolved
   - No blocking comments

4. **Status Checks:**
   - All required status checks must pass

### Blocking Conditions

- ❌ Pipeline failures in required jobs
- ❌ Missing approvals
- ❌ Unresolved discussions
- ❌ Failed status checks
- ❌ Merge conflicts
- ❌ Protected branch rules violation

---

## Auto-Tag Behavior

### Current Behavior
- Runs on push to main
- Creates tag automatically
- Tag triggers release

### New Behavior (After Implementation)
- **Only runs after MR merge** (push to main from MR)
- Includes MR number in tag message (if available)
- Creates tag: `vYYYY.MM.DD.MICRO`
- Tag push triggers release job

### Tag Message Format

**Standard:**
```
Release 2026.01.20.1
```

**With MR:**
```
Release 2026.01.20.1 (merged from MR !123)
```

---

## Release Behavior

### Current Behavior
- Runs on tag push
- Publishes to PyPI

### New Behavior (After Implementation)
- **Unchanged** - Still runs on tag push
- Triggered by auto-tag job after MR merge
- Publishes to PyPI as before

---

## Rollback Plan

If issues arise:

1. **Temporary Rollback:**
   - Revert `.gitlab-ci.yml` changes
   - Remove protected branch settings
   - Allow direct pushes temporarily

2. **Partial Rollback:**
   - Keep MR pipelines
   - Allow direct pushes to main
   - Disable auto-tag temporarily

3. **Full Rollback:**
   - Revert all changes
   - Restore original workflow
   - Remove new jobs

---

## Migration Checklist

### Pre-Implementation
- [ ] Review and understand new workflow
- [ ] Communicate changes to team
- [ ] Backup current `.gitlab-ci.yml`
- [ ] Document current workflow (for reference)

### Implementation
- [ ] Update `.gitlab-ci.yml` with new stages
- [ ] Add `pre-commit` job
- [ ] Add `lint` job
- [ ] Add `sast-bandit` job
- [ ] Add `dependency-scanning` job
- [ ] Add `secret-detection` job
- [ ] Add `code-quality` job
- [ ] Update `test` job rules
- [ ] Update `auto-tag` job rules
- [ ] Create MR template
- [ ] Protect main branch
- [ ] Configure merge request requirements
- [ ] Set required jobs

### Testing
- [ ] Create test branch
- [ ] Push test branch
- [ ] Create test MR
- [ ] Verify all jobs run
- [ ] Verify jobs can pass
- [ ] Merge test MR
- [ ] Verify auto-tag runs
- [ ] Verify release runs
- [ ] Clean up test branch and tag

### Documentation
- [ ] Update README.md
- [ ] Create CONTRIBUTING.md
- [ ] Update troubleshooting guide
- [ ] Document branch naming conventions
- [ ] Create workflow diagram (optional)

### Team Communication
- [ ] Announce workflow changes
- [ ] Provide training/documentation
- [ ] Set up office hours for questions
- [ ] Monitor first few MRs for issues

---

## Expected Benefits

1. **Code Quality:**
   - Catch issues before merge
   - Enforce coding standards
   - Maintain test coverage

2. **Security:**
   - Detect vulnerabilities early
   - Prevent secret leaks
   - Scan dependencies

3. **Compliance:**
   - License compliance checks
   - Documentation requirements
   - Audit trail via MRs

4. **Collaboration:**
   - Code review required
   - Knowledge sharing
   - Better change tracking

5. **Reliability:**
   - Automated testing
   - Consistent release process
   - Reduced manual errors

---

## Troubleshooting

### Common Issues

#### Issue: MR Pipeline Not Running

**Symptoms:**
- No pipeline triggered when creating MR

**Solutions:**
1. Verify `.gitlab-ci.yml` has jobs with `merge_request_event` rules
2. Check branch is pushed to remote
3. Verify MR is created (not just branch exists)
4. Check CI/CD settings → Pipeline triggers

#### Issue: Required Jobs Not Blocking Merge

**Symptoms:**
- Can merge even when jobs fail

**Solutions:**
1. Settings → CI/CD → Pipeline → Required jobs
2. Add jobs to required list
3. Verify "Pipeline must succeed" is enabled
4. Check merge request settings

#### Issue: Auto-Tag Not Running After Merge

**Symptoms:**
- MR merged but no tag created

**Solutions:**
1. Verify `auto-tag` job rules include `CI_PIPELINE_SOURCE == "push"`
2. Check `CI_COMMIT_BRANCH == "main"`
3. Verify GITLAB_TOKEN is configured
4. Check job logs for errors

#### Issue: Pre-Commit Job Fails

**Symptoms:**
- Pre-commit hooks fail in CI

**Solutions:**
1. Run `pre-commit run --all-files` locally first
2. Fix formatting/linting issues
3. Commit fixes
4. Push updated branch

---

## References

- [GitLab Merge Request Pipelines](https://docs.gitlab.com/ee/ci/pipelines/merge_request_pipelines.html)
- [GitLab Protected Branches](https://docs.gitlab.com/ee/user/project/protected_branches.html)
- [GitLab Merge Request Approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [GitLab Required Jobs](https://docs.gitlab.com/ee/ci/pipelines/settings.html#required-jobs)
- [Pre-commit Hooks](https://pre-commit.com/)

---

*Last updated: 2026-01-20*
