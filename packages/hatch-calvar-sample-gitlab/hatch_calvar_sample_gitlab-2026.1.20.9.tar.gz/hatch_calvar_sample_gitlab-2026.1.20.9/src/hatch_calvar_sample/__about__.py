# SPDX-FileCopyrightText: 2026-present QAToolist <qatoolist@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Version metadata for hatch_calvar_sample package."""

# Import version function with fallback for Python < 3.8
try:
    from importlib.metadata import version as _version_func
except ImportError:
    # Python < 3.8
    from importlib_metadata import (
        version as _version_func,  # type: ignore[no-untyped-call]
    )


def get_package_version(package_name: str) -> str:
    """Get version from package metadata."""
    return _version_func(package_name)


# Try to get version from package metadata (when installed)
try:
    __version__ = get_package_version("hatch-calvar-sample-gitlab")
except Exception:
    # Fallback: try reading from VERSION file (for development builds)
    import os
    from pathlib import Path

    version_file = Path(__file__).parent / "VERSION"
    if version_file.exists():
        __version__ = version_file.read_text().strip()
    else:
        # Last resort: read from environment variable
        __version__ = os.environ.get("HATCH_CALVER_VERSION", "0.0.0.dev0")
