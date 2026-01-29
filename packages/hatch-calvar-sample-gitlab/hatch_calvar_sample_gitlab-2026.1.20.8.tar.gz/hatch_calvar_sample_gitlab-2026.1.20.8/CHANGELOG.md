# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Calendar Versioning (CalVer)](https://calver.org/) with format `YYYY.MM.DD.MICRO`.

## [Unreleased]

## [2024.01.18.1] - 2024-01-18

### Added
- Initial implementation of CalVer versioning system
- Version calculation script (`scripts/calc_version.py`)
  - Calculates next CalVer version from git tags
  - Supports both `vYYYY.MM.DD.MICRO` and `YYYY.MM.DD.MICRO` tag formats
  - Validates version format and PEP 440 compliance
- Version checking CLI tool (`calver-check`)
  - `calc` command: Calculate next version
  - `check` command: Check version from multiple sources
  - `validate` command: Validate version format
  - `compare` command: Compare two versions
  - `info` command: Show version information
  - JSON output support for all commands
- Dynamic versioning with hatch
  - VERSION file-based versioning
  - Version reading from `importlib.metadata` with fallbacks
- GitLab CI/CD release pipeline
  - Automated PyPI publishing on tag push
  - Version format validation
  - Package building and validation with twine
- Unit tests for version calculation and CLI
- Comprehensive documentation in README.md
- Makefile with convenient targets for common tasks

### Configuration
- Hatch build system with dynamic versioning
- Python 3.8+ support
- MIT license

[Unreleased]: https://gitlab.com/QAToolist/hatch-calvar-sample-gitlab/-/compare/v2024.01.18.1...HEAD
[2024.01.18.1]: https://gitlab.com/QAToolist/hatch-calvar-sample-gitlab/-/tags/v2024.01.18.1
