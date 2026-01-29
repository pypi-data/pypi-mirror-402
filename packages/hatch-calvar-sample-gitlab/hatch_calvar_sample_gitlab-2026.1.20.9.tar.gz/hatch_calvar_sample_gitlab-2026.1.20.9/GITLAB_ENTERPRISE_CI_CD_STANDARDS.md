# GitLab Enterprise CI/CD Standards Guide

This document outlines additional CI/CD enhancements to meet GitLab Enterprise project standards, including security, compliance, quality gates, and operational excellence.

## Table of Contents

- [Security Scanning](#security-scanning)
- [Code Quality & Linting](#code-quality--linting)
- [Dependency Management](#dependency-management)
- [Compliance & Governance](#compliance--governance)
- [Pipeline Optimization](#pipeline-optimization)
- [Artifact Management](#artifact-management)
- [Environment Protection](#environment-protection)
- [Merge Request Requirements](#merge-request-requirements)
- [Audit & Compliance](#audit--compliance)
- [Performance & Monitoring](#performance--monitoring)
- [Implementation Checklist](#implementation-checklist)

---

## Security Scanning

### 1. Static Application Security Testing (SAST)

**Purpose:** Detect security vulnerabilities in source code.

**GitLab Native Integration:**
```yaml
include:
  - template: Security/SAST.gitlab-ci.yml

sast:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
```

**Custom Implementation (Bandit for Python):**
```yaml
sast-bandit:
  stage: test
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

### 2. Dependency Scanning

**Purpose:** Identify vulnerable dependencies.

**GitLab Native Integration:**
```yaml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml

dependency_scanning:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
```

**Custom Implementation:**
```yaml
dependency-scanning:
  stage: test
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

### 3. Secret Detection

**Purpose:** Prevent secrets from being committed.

**GitLab Native Integration:**
```yaml
include:
  - template: Security/Secret-Detection.gitlab-ci.yml

secret_detection:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
```

**Custom Implementation (Gitleaks):**
```yaml
secret-detection:
  stage: test
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

### 4. Container Scanning (if using containers)

**Purpose:** Scan container images for vulnerabilities.

```yaml
include:
  - template: Security/Container-Scanning.gitlab-ci.yml

container_scanning:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
```

### 5. License Scanning

**Purpose:** Detect license compliance issues.

**GitLab Native Integration:**
```yaml
include:
  - template: Security/License-Scanning.gitlab-ci.yml

license_scanning:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
```

**Enhancement to existing license-check job:**
```yaml
license-scanning:
  stage: test
  image: python:3.11
  script:
    - pip install pip-licenses licensecheck
    - pip install -e .
    - |
      echo "=== License Scanning ==="
      pip-licenses --format=json --output-file=license-scan-report.json
      pip-licenses --format=spdx-json --output-file=license-spdx.json
      # Check for prohibited licenses
      pip-licenses --fail-on="GPL;AGPL" || exit 1
  artifacts:
    reports:
      license_scanning: license-scan-report.json
    paths:
      - license-scan-report.json
      - license-spdx.json
    expire_in: 30 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

---

## Code Quality & Linting

### 1. Code Quality Analysis

**Purpose:** Measure code quality metrics.

**GitLab Native Integration:**
```yaml
include:
  - template: Code-Quality.gitlab-ci.yml

code_quality:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
```

**Custom Implementation:**
```yaml
code-quality:
  stage: test
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

### 2. Linting & Formatting

**Enhancement to existing setup:**
```yaml
lint:
  stage: test
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
  artifacts:
    paths:
      - .ruff_cache/
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

### 3. Documentation Quality

```yaml
docs-quality:
  stage: test
  image: python:3.11
  script:
    - pip install interrogate pydocstyle
    - |
      echo "=== Docstring Coverage ==="
      interrogate src/ -v --fail-under=80 || exit 1
    - |
      echo "=== Docstring Style ==="
      pydocstyle src/ --convention=numpy --add-ignore=D100,D104,D105,D107 || exit 1
  artifacts:
    paths:
      - docs-coverage-report.html
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: true
```

---

## Dependency Management

### 1. Dependency Update Scanning

**Purpose:** Automatically detect outdated dependencies.

```yaml
dependency-update-check:
  stage: test
  image: python:3.11
  script:
    - pip install pip-audit pipdeptree
    - |
      echo "=== Dependency Tree ==="
      pipdeptree --json-tree > dependency-tree.json
    - |
      echo "=== Outdated Packages ==="
      pip list --outdated --format=json > outdated-packages.json || true
  artifacts:
    paths:
      - dependency-tree.json
      - outdated-packages.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: true
```

### 2. Dependency Review

**GitLab Native Integration:**
```yaml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml

dependency_scanning:
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

---

## Compliance & Governance

### 1. Compliance Pipeline

**Purpose:** Ensure regulatory compliance.

```yaml
compliance-check:
  stage: test
  image: python:3.11
  script:
    - |
      echo "=== Compliance Checks ==="
      # Check for required files
      test -f LICENSE.txt || (echo "ERROR: LICENSE.txt missing" && exit 1)
      test -f CHANGELOG.md || (echo "ERROR: CHANGELOG.md missing" && exit 1)
      test -f README.md || (echo "ERROR: README.md missing" && exit 1)

      # Check license is present in pyproject.toml
      grep -q "license.*MIT" pyproject.toml || (echo "ERROR: License not specified" && exit 1)

      # Check for required metadata
      python -c "import tomli; data = tomli.load(open('pyproject.toml')); assert 'project' in data; assert 'authors' in data['project']"

      echo "✓ Compliance checks passed"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: false
```

### 2. SBOM Generation

**Purpose:** Generate Software Bill of Materials for compliance.

```yaml
sbom-generation:
  stage: test
  image: python:3.11
  script:
    - pip install cyclonedx-bom pip-licenses
    - pip install -e .
    - |
      echo "=== Generating SBOM ==="
      # Generate CycloneDX SBOM
      cyclonedx-py -o sbom-cyclonedx.json
      # Generate SPDX SBOM
      pip-licenses --format=spdx-json --output-file=sbom-spdx.json
  artifacts:
    paths:
      - sbom-cyclonedx.json
      - sbom-spdx.json
    expire_in: 90 days
  rules:
    - if: $CI_COMMIT_TAG =~ /^v.*$/
  allow_failure: false
```

---

## Pipeline Optimization

### 1. Parallel Execution

**Current:** Already using parallel matrix for tests.

**Enhancement:** Add more parallel jobs:
```yaml
stages:
  - validate
  - test
  - security
  - build
  - release

# Run security scans in parallel
security:
  stage: security
  parallel:
    - sast-bandit
    - dependency-scanning
    - secret-detection
    - license-scanning
```

### 2. Pipeline Caching

**Enhancement to existing cache:**
```yaml
cache:
  key:
    files:
      - pyproject.toml
      - requirements*.txt
  paths:
    - .cache/pip
    - .venv/
    - .ruff_cache/
    - .mypy_cache/
  policy: pull-push
```

### 3. Conditional Execution

```yaml
# Only run expensive jobs on main/master or MRs
expensive-analysis:
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_TAG
```

### 4. Pipeline Schedules

**Purpose:** Regular security scans and dependency updates.

Configure in GitLab UI: CI/CD → Schedules

Example schedules:
- **Daily Security Scan:** Run all security jobs daily
- **Weekly Dependency Update:** Check for dependency updates weekly
- **Monthly Compliance Audit:** Run full compliance checks monthly

---

## Artifact Management

### 1. Artifact Retention Policies

**Enhancement:**
```yaml
artifacts:
  paths:
    - dist/
  expire_in: 90 days  # Keep releases longer
  reports:
    junit: junit.xml
    coverage_report:
      coverage_format: cobertura
      path: coverage.xml
```

### 2. Release Artifacts

```yaml
release-artifacts:
  stage: release
  script:
    - echo "Collecting release artifacts..."
    - mkdir -p release-artifacts
    - cp dist/* release-artifacts/
    - cp LICENSE.txt release-artifacts/
    - cp README.md release-artifacts/
    - cp CHANGELOG.md release-artifacts/
  artifacts:
    paths:
      - release-artifacts/
    expire_in: 1 year
  rules:
    - if: $CI_COMMIT_TAG =~ /^v.*$/
```

### 3. Package Registry

**Purpose:** Store built packages in GitLab Package Registry.

```yaml
publish-to-registry:
  stage: release
  image: python:3.11
  script:
    - |
      # Publish to GitLab Package Registry
      TWINE_PASSWORD=${CI_JOB_TOKEN} \
      TWINE_USERNAME=gitlab-ci-token \
      twine upload \
        --repository-url ${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/pypi \
        dist/*
  rules:
    - if: $CI_COMMIT_TAG =~ /^v.*$/
```

---

## Environment Protection

### 1. Protected Environments

Configure in GitLab UI: Settings → CI/CD → Protected Environments

- **Production:** Require manual approval
- **Staging:** Auto-deploy from develop branch
- **Release:** Protected, requires maintainer approval

### 2. Environment-Specific Variables

```yaml
release:
  environment:
    name: production
    url: https://pypi.org/project/hatch-calvar-sample-gitlab/
    deployment_tier: production
  rules:
    - if: $CI_COMMIT_TAG =~ /^v.*$/
```

### 3. Deployment Gates

```yaml
deploy-approval:
  stage: release
  environment:
    name: production
    action: start
  script:
    - echo "Waiting for approval..."
  when: manual
  rules:
    - if: $CI_COMMIT_TAG =~ /^v.*$/
```

---

## Merge Request Requirements

### 1. Merge Request Pipelines

**Already configured** - ensure all jobs run on MRs:
```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### 2. Required Jobs for Merge

Configure in GitLab UI: Settings → Merge Requests → Merge Checks

Required jobs:
- ✅ test (all Python versions)
- ✅ lint
- ✅ sast-bandit
- ✅ dependency-scanning
- ✅ secret-detection
- ✅ code-quality
- ✅ build-verify

### 3. Merge Request Approvals

Configure in GitLab UI: Settings → Merge Requests → Approval Rules

- **Security Review:** Require approval from security team
- **Code Review:** Require 2 approvals
- **Maintainer Approval:** Required for protected branches

### 4. Merge Request Templates

Create `.gitlab/merge_request_templates/default.md`:
```markdown
## Description
<!-- Describe your changes -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated existing tests

## Security
- [ ] No secrets committed
- [ ] Dependencies reviewed
- [ ] Security scan passed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] License compliance verified
```

---

## Audit & Compliance

### 1. Pipeline Audit Logs

Enable in GitLab UI: Settings → CI/CD → Pipeline Logs

### 2. Compliance Framework

Configure in GitLab UI: Settings → General → Compliance Frameworks

Add compliance framework:
- **SOC 2**
- **ISO 27001**
- **GDPR**
- **HIPAA** (if applicable)

### 3. Audit Events

Monitor in GitLab UI: Security & Compliance → Audit Events

Track:
- Pipeline executions
- Variable access
- Deployment approvals
- Merge request approvals

### 4. Compliance Pipeline

```yaml
compliance-audit:
  stage: test
  script:
    - |
      echo "=== Compliance Audit ==="
      # Check for required documentation
      # Verify license compliance
      # Check security policies
      # Validate metadata
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
    - schedule
  allow_failure: false
```

---

## Performance & Monitoring

### 1. Performance Testing

```yaml
performance-test:
  stage: test
  image: python:3.11
  script:
    - pip install pytest-benchmark
    - pytest tests/ --benchmark-only --benchmark-json=benchmark.json
  artifacts:
    paths:
      - benchmark.json
    expire_in: 1 week
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: true
```

### 2. Load Testing

```yaml
load-test:
  stage: test
  image: python:3.11
  script:
    - pip install locust
    - locust --headless --users 100 --spawn-rate 10 --run-time 60s
  rules:
    - if: $CI_COMMIT_BRANCH == "main" || $CI_COMMIT_BRANCH == "master"
  allow_failure: true
```

### 3. Pipeline Performance Monitoring

Monitor in GitLab UI: CI/CD → Pipelines → Pipeline Efficiency

Track:
- Job duration
- Pipeline duration
- Cache hit rates
- Artifact sizes

---

## Additional Enterprise Features

### 1. GitLab Security Dashboard

Enable in GitLab UI: Security & Compliance → Security Dashboard

Aggregates:
- SAST findings
- Dependency vulnerabilities
- Secret detection results
- License compliance issues

### 2. Vulnerability Management

Enable in GitLab UI: Security & Compliance → Vulnerability Report

Features:
- Track vulnerabilities over time
- Assign remediation
- Track false positives
- Generate reports

### 3. License Compliance

Enable in GitLab UI: Security & Compliance → License Compliance

Features:
- Track license usage
- Policy enforcement
- License approval workflow

### 4. Security Policies

Create `.gitlab/security-policies/policy.yml`:
```yaml
scan_execution_policy:
  - name: Enforce SAST on all MRs
    rules:
      - type: merge_request
    actions:
      - scan: sast
```

### 5. Compliance Frameworks

Configure in GitLab UI: Settings → General → Compliance Frameworks

Add labels and policies for:
- SOC 2
- ISO 27001
- GDPR
- HIPAA

---

## Implementation Checklist

### Phase 1: Security (Critical)
- [ ] Add SAST scanning (Bandit)
- [ ] Add dependency scanning (Safety, pip-audit)
- [ ] Add secret detection (Gitleaks)
- [ ] Add license scanning
- [ ] Configure security dashboard
- [ ] Set up vulnerability management

### Phase 2: Quality (High Priority)
- [ ] Enhance linting job (fail on errors)
- [ ] Add code quality analysis (Radon, Xenon)
- [ ] Add documentation quality checks
- [ ] Set up code quality gates
- [ ] Configure merge request requirements

### Phase 3: Compliance (Medium Priority)
- [ ] Add compliance checks
- [ ] Generate SBOM
- [ ] Set up compliance framework
- [ ] Configure audit logging
- [ ] Add compliance pipeline

### Phase 4: Optimization (Low Priority)
- [ ] Optimize pipeline caching
- [ ] Add parallel execution
- [ ] Set up pipeline schedules
- [ ] Configure artifact retention
- [ ] Add performance monitoring

### Phase 5: Advanced Features
- [ ] Set up protected environments
- [ ] Configure deployment approvals
- [ ] Add performance testing
- [ ] Set up load testing
- [ ] Configure package registry

---

## Configuration Files

### .gitlab-ci.yml Structure

```yaml
stages:
  - validate      # Quick checks
  - test          # Unit/integration tests
  - security      # Security scanning
  - quality       # Code quality
  - build         # Build verification
  - compliance    # Compliance checks
  - release       # Release and deploy

include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/License-Scanning.gitlab-ci.yml
  - template: Code-Quality.gitlab-ci.yml

# Your custom jobs...
```

### GitLab Project Settings

**Settings → CI/CD:**
- Enable "Auto DevOps"
- Configure "Pipeline triggers"
- Set up "Pipeline schedules"
- Configure "Protected environments"
- Set "Pipeline logs" retention

**Settings → Merge Requests:**
- Configure "Merge checks"
- Set up "Approval rules"
- Enable "Merge request approvals"

**Settings → Repository:**
- Protect branches (main, master)
- Protect tags (v*)
- Configure "Push rules"

**Security & Compliance:**
- Enable "Security Dashboard"
- Configure "Vulnerability Management"
- Set up "License Compliance"
- Configure "Security Policies"

---

## Best Practices Summary

1. **Security First:**
   - Run security scans on every MR
   - Fail pipeline on high/critical vulnerabilities
   - Require security team approval for security changes

2. **Quality Gates:**
   - Enforce code quality thresholds
   - Require test coverage minimums
   - Block merges on linting failures

3. **Compliance:**
   - Generate SBOM for all releases
   - Track license compliance
   - Maintain audit logs

4. **Performance:**
   - Optimize pipeline execution time
   - Use caching effectively
   - Monitor pipeline metrics

5. **Governance:**
   - Protect production environments
   - Require approvals for releases
   - Maintain documentation

---

## References

- [GitLab Security Scanning](https://docs.gitlab.com/ee/user/application_security/)
- [GitLab Compliance](https://docs.gitlab.com/ee/user/compliance/)
- [GitLab CI/CD Best Practices](https://docs.gitlab.com/ee/ci/pipelines/pipeline_efficiency.html)
- [GitLab Merge Request Approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [GitLab Protected Environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

---

*Last updated: 2026-01-20*
