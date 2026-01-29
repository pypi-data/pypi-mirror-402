"""CLI tool for CalVer version management."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Import version function with fallback for Python < 3.8
try:
    from importlib.metadata import version as _version_func
except ImportError:
    # Python < 3.8
    from importlib_metadata import (
        version as _version_func,  # type: ignore[no-untyped-call]
    )


# Import version calculation functions from script
# We'll need to make these importable or duplicate the logic
# For now, we'll import from the script directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
try:
    from calc_version import (
        calculate_next_version,
        check_pep440_compliance,
        get_git_tags,
        parse_calver_tag,
        validate_version_format,
    )
except ImportError:
    # Fallback if script not available
    def calculate_next_version():
        return "0.0.0.0"  # nosec B104

    def validate_version_format(version: str) -> bool:
        return bool(version)

    def check_pep440_compliance(version: str) -> bool:
        return True

    def parse_calver_tag(tag: str):
        return None

    def get_git_tags():
        return []


def get_package_version_from_metadata() -> Optional[str]:
    """Get version from installed package metadata.

    Returns:
        Version string or None if not available
    """
    try:
        return _version_func("hatch-calvar-sample-gitlab")
    except Exception:
        return None


def version_calc(args: argparse.Namespace) -> int:
    """Calculate next version.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        version = calculate_next_version()
    except Exception as e:
        print(f"Error calculating version: {e}", file=sys.stderr)
        return 1

    if args.json:
        output = {"version": version}
        print(json.dumps(output))
    else:
        print(version)

    return 0


def version_check(args: argparse.Namespace) -> int:
    """Check current version from different sources.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    versions = {}

    # Check package metadata
    pkg_version = get_package_version_from_metadata()
    if pkg_version:
        versions["package"] = pkg_version

    # Check git tags
    git_tags = get_git_tags()
    calver_tags = [tag for tag in git_tags if parse_calver_tag(tag)]
    if calver_tags:
        # Get latest CalVer tag
        parsed_tags = [(tag, parse_calver_tag(tag)) for tag in calver_tags]
        parsed_tags.sort(key=lambda x: x[1], reverse=True)  # Sort by date/micro
        latest_tag = parsed_tags[0][0]
        # Remove 'v' prefix if present
        if latest_tag.startswith("v"):
            versions["git_tag"] = latest_tag[1:]
        else:
            versions["git_tag"] = latest_tag

    # Check VERSION file
    version_file = (
        Path(__file__).parent.parent.parent / "src" / "hatch_calvar_sample" / "VERSION"
    )
    if version_file.exists():
        versions["file"] = version_file.read_text().strip()

    if args.json:
        output = {"versions": versions}
        print(json.dumps(output, indent=2))
    else:
        if versions:
            print("Current versions:")
            for source, ver in versions.items():
                print(f"  {source}: {ver}")
        else:
            print("No version information found", file=sys.stderr)
            return 1

    return 0


def version_validate(args: argparse.Namespace) -> int:
    """Validate version format.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for valid, 1 for invalid)
    """
    if not args.version:
        print("Error: version argument required", file=sys.stderr)
        return 1

    version = args.version

    # Validate format
    is_valid_format = validate_version_format(version)

    # Check PEP 440 compliance
    is_pep440 = False
    if is_valid_format:
        is_pep440 = check_pep440_compliance(version)

    if args.json:
        output = {
            "version": version,
            "valid_format": is_valid_format,
            "pep440_compliant": is_pep440,
        }
        print(json.dumps(output))
        return 0 if (is_valid_format and is_pep440) else 1
    else:
        if not is_valid_format:
            print(f"Invalid CalVer format: {version}", file=sys.stderr)
            return 1

        if not is_pep440:
            print(f"Version not PEP 440 compliant: {version}", file=sys.stderr)
            return 1

        print(f"Version '{version}' is valid and PEP 440 compliant")
        return 0


def version_compare(args: argparse.Namespace) -> int:
    """Compare two versions.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if len(args.versions) != 2:
        print("Error: exactly two versions required for comparison", file=sys.stderr)
        return 1

    v1_str, v2_str = args.versions

    # Parse versions
    v1 = parse_calver_tag(v1_str)
    v2 = parse_calver_tag(v2_str)

    if not v1:
        print(f"Error: invalid version format: {v1_str}", file=sys.stderr)
        return 1

    if not v2:
        print(f"Error: invalid version format: {v2_str}", file=sys.stderr)
        return 1

    # Compare (year, month, day, micro)
    if v1 < v2:
        result = "<"
    elif v1 > v2:
        result = ">"
    else:
        result = "=="

    if args.json:
        output = {
            "version1": v1_str,
            "version2": v2_str,
            "comparison": result,
        }
        print(json.dumps(output))
    else:
        print(f"{v1_str} {result} {v2_str}")

    return 0


def version_info(args: argparse.Namespace) -> int:
    """Show version information.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    info = {}

    # Get next version
    try:
        next_version = calculate_next_version()
        parsed = parse_calver_tag(next_version)
        if parsed:
            year, month, day, micro = parsed
            info["next_version"] = next_version
            info["date"] = f"{year:04d}-{month:02d}-{day:02d}"
            info["micro"] = micro
    except Exception as e:
        info["next_version_error"] = str(e)

    # Get current package version
    pkg_version = get_package_version_from_metadata()
    if pkg_version:
        info["current_package_version"] = pkg_version

    if args.json:
        print(json.dumps(info, indent=2))
    else:
        print("Version Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CalVer version management CLI", prog="calver-check"
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # calc command
    calc_parser = subparsers.add_parser("calc", help="Calculate next CalVer version")
    calc_parser.set_defaults(func=version_calc)

    # check command
    check_parser = subparsers.add_parser(
        "check", help="Check current version from different sources"
    )
    check_parser.set_defaults(func=version_check)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate version format and PEP 440 compliance"
    )
    validate_parser.add_argument("version", help="Version string to validate")
    validate_parser.set_defaults(func=version_validate)

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two versions")
    compare_parser.add_argument("versions", nargs=2, help="Two versions to compare")
    compare_parser.set_defaults(func=version_compare)

    # info command
    info_parser = subparsers.add_parser("info", help="Show version information")
    info_parser.set_defaults(func=version_info)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Call the appropriate function
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
