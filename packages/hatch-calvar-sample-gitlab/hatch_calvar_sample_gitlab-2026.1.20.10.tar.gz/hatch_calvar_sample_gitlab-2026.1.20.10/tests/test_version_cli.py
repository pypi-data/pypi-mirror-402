"""Tests for version checking CLI tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from hatch_calvar_sample import cli  # noqa: E402


class TestVersionCalc:
    """Test version calculation command."""

    @patch("hatch_calvar_sample.cli.calculate_next_version")
    def test_version_calc_success(self, mock_calc):
        """Test version calc command success."""
        mock_calc.return_value = "2024.01.18.1"

        args = MagicMock()
        args.json = False

        result = cli.version_calc(args)

        assert result == 0
        mock_calc.assert_called_once()

    @patch("hatch_calvar_sample.cli.calculate_next_version")
    def test_version_calc_json_output(self, mock_calc):
        """Test version calc command with JSON output."""
        mock_calc.return_value = "2024.01.18.1"

        args = MagicMock()
        args.json = True

        result = cli.version_calc(args)

        assert result == 0


class TestVersionCheck:
    """Test version check command."""

    @patch("hatch_calvar_sample.cli.get_package_version_from_metadata")
    @patch("hatch_calvar_sample.cli.get_git_tags")
    def test_version_check_package_version(self, mock_tags, mock_pkg_version):
        """Test version check with package version available."""
        mock_pkg_version.return_value = "2024.01.18.1"
        mock_tags.return_value = []

        args = MagicMock()
        args.json = False

        result = cli.version_check(args)

        assert result == 0

    @patch("hatch_calvar_sample.cli.get_package_version_from_metadata")
    @patch("hatch_calvar_sample.cli.get_git_tags")
    @patch.object(Path, "exists", return_value=False)
    def test_version_check_no_versions(
        self, mock_path_exists, mock_tags, mock_pkg_version
    ):
        """Test version check with no versions available."""
        mock_pkg_version.return_value = None
        mock_tags.return_value = []
        # Mock VERSION file to not exist

        args = MagicMock()
        args.json = False

        result = cli.version_check(args)

        # Should return 1 when no versions found
        assert result == 1


class TestVersionValidate:
    """Test version validate command."""

    @patch("hatch_calvar_sample.cli.validate_version_format")
    @patch("hatch_calvar_sample.cli.check_pep440_compliance")
    def test_version_validate_valid(self, mock_pep440, mock_validate):
        """Test version validate with valid version."""
        mock_validate.return_value = True
        mock_pep440.return_value = True

        args = MagicMock()
        args.version = "2024.01.18.1"
        args.json = False

        result = cli.version_validate(args)

        assert result == 0

    @patch("hatch_calvar_sample.cli.validate_version_format")
    def test_version_validate_invalid_format(self, mock_validate):
        """Test version validate with invalid format."""
        mock_validate.return_value = False

        args = MagicMock()
        args.version = "invalid"
        args.json = False

        result = cli.version_validate(args)

        assert result == 1

    def test_version_validate_missing_version(self):
        """Test version validate with missing version argument."""
        args = MagicMock()
        args.version = None

        result = cli.version_validate(args)

        assert result == 1


class TestVersionCompare:
    """Test version compare command."""

    @patch("hatch_calvar_sample.cli.parse_calver_tag")
    def test_version_compare_less_than(self, mock_parse):
        """Test version compare with v1 < v2."""
        mock_parse.side_effect = [(2024, 1, 18, 1), (2024, 1, 18, 2)]

        args = MagicMock()
        args.versions = ["2024.01.18.1", "2024.01.18.2"]
        args.json = False

        result = cli.version_compare(args)

        assert result == 0

    @patch("hatch_calvar_sample.cli.parse_calver_tag")
    def test_version_compare_equal(self, mock_parse):
        """Test version compare with v1 == v2."""
        mock_parse.return_value = (2024, 1, 18, 1)

        args = MagicMock()
        args.versions = ["2024.01.18.1", "2024.01.18.1"]
        args.json = False

        result = cli.version_compare(args)

        assert result == 0

    @patch("hatch_calvar_sample.cli.parse_calver_tag")
    def test_version_compare_invalid_version(self, mock_parse):
        """Test version compare with invalid version."""
        mock_parse.side_effect = [(2024, 1, 18, 1), None]

        args = MagicMock()
        args.versions = ["2024.01.18.1", "invalid"]
        args.json = False

        result = cli.version_compare(args)

        assert result == 1

    def test_version_compare_wrong_number_of_versions(self):
        """Test version compare with wrong number of versions."""
        args = MagicMock()
        args.versions = ["2024.01.18.1"]  # Only one version

        result = cli.version_compare(args)

        assert result == 1


class TestVersionInfo:
    """Test version info command."""

    @patch("hatch_calvar_sample.cli.calculate_next_version")
    @patch("hatch_calvar_sample.cli.get_package_version_from_metadata")
    def test_version_info_success(self, mock_pkg_version, mock_calc):
        """Test version info command success."""
        mock_calc.return_value = "2024.01.18.2"
        mock_pkg_version.return_value = "2024.01.18.1"

        args = MagicMock()
        args.json = False

        result = cli.version_info(args)

        assert result == 0


if __name__ == "__main__":
    pytest.main([__file__])
