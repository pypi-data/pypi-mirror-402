"""Tests for version calculation script."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from calc_version import (  # noqa: E402
    calculate_next_version,
    check_pep440_compliance,
    get_current_date,
    get_git_tags,
    parse_calver_tag,
    validate_version_format,
)


class TestParseCalverTag:
    """Test CalVer tag parsing."""

    def test_parse_valid_tag_with_v_prefix(self):
        """Test parsing valid tag with 'v' prefix."""
        result = parse_calver_tag("v2024.01.18.1")
        assert result == (2024, 1, 18, 1)

    def test_parse_valid_tag_without_v_prefix(self):
        """Test parsing valid tag without 'v' prefix."""
        result = parse_calver_tag("2024.01.18.1")
        assert result == (2024, 1, 18, 1)

    def test_parse_invalid_tag_format(self):
        """Test parsing invalid tag format."""
        assert parse_calver_tag("2024.1.18.1") is None
        assert parse_calver_tag("v1.2.3") is None
        assert parse_calver_tag("2024.01.18") is None
        assert parse_calver_tag("invalid") is None

    def test_parse_invalid_date_values(self):
        """Test parsing tags with invalid date values."""
        assert parse_calver_tag("2024.13.18.1") is None  # Month > 12
        assert parse_calver_tag("2024.00.18.1") is None  # Month < 1
        assert parse_calver_tag("2024.01.32.1") is None  # Day > 31
        assert parse_calver_tag("2024.01.00.1") is None  # Day < 1

    def test_parse_invalid_micro(self):
        """Test parsing tag with invalid micro value."""
        assert parse_calver_tag("2024.01.18.0") is None  # Micro < 1


class TestValidateVersionFormat:
    """Test version format validation."""

    def test_validate_valid_versions(self):
        """Test validating valid version formats."""
        assert validate_version_format("2024.01.18.1") is True
        assert validate_version_format("v2024.01.18.1") is True
        assert validate_version_format("2024.12.31.999") is True

    def test_validate_invalid_versions(self):
        """Test validating invalid version formats."""
        assert validate_version_format("2024.1.18.1") is False
        assert validate_version_format("1.2.3") is False
        assert validate_version_format("invalid") is False


class TestGetCurrentDate:
    """Test getting current date."""

    def test_get_current_date_format(self):
        """Test that current date returns (year, month, day) tuple."""
        date = get_current_date()
        assert len(date) == 3
        year, month, day = date
        assert isinstance(year, int)
        assert isinstance(month, int)
        assert isinstance(day, int)
        assert 1 <= month <= 12
        assert 1 <= day <= 31


class TestGetGitTags:
    """Test getting git tags."""

    @patch("calc_version.subprocess.run")
    def test_get_git_tags_success(self, mock_run):
        """Test getting git tags successfully."""
        mock_run.return_value = MagicMock(
            stdout="v2024.01.18.1\n2024.01.17.5\ntag1\n", returncode=0
        )
        tags = get_git_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0

    @patch("calc_version.subprocess.run")
    def test_get_git_tags_failure(self, mock_run):
        """Test handling git tags failure gracefully."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        tags = get_git_tags()
        assert tags == []


class TestCalculateNextVersion:
    """Test calculating next version."""

    @patch("calc_version.get_git_tags")
    @patch("calc_version.get_current_date")
    def test_calculate_next_version_no_tags(self, mock_date, mock_tags):
        """Test calculating next version with no existing tags."""
        mock_date.return_value = (2024, 1, 18)
        mock_tags.return_value = []

        version = calculate_next_version()

        assert version == "2024.01.18.1"
        assert validate_version_format(version)

    @patch("calc_version.get_git_tags")
    @patch("calc_version.get_current_date")
    def test_calculate_next_version_with_tags_same_date(self, mock_date, mock_tags):
        """Test calculating next version with tags on same date."""
        mock_date.return_value = (2024, 1, 18)
        mock_tags.return_value = ["v2024.01.18.1", "v2024.01.18.2"]

        version = calculate_next_version()

        assert version == "2024.01.18.3"

    @patch("calc_version.get_git_tags")
    @patch("calc_version.get_current_date")
    def test_calculate_next_version_with_tags_different_date(
        self, mock_date, mock_tags
    ):
        """Test calculating next version with tags on different date."""
        mock_date.return_value = (2024, 1, 19)
        mock_tags.return_value = ["v2024.01.18.1", "v2024.01.18.5"]

        version = calculate_next_version()

        # Should reset to 1 for new date
        assert version == "2024.01.19.1"

    @patch("calc_version.get_git_tags")
    @patch("calc_version.get_current_date")
    def test_calculate_next_version_ignores_invalid_tags(self, mock_date, mock_tags):
        """Test that invalid tags are ignored."""
        mock_date.return_value = (2024, 1, 18)
        mock_tags.return_value = ["invalid-tag", "v2024.01.18.1", "not-a-version"]

        version = calculate_next_version()

        # Should increment based on valid tag
        assert version == "2024.01.18.2"


class TestPEP440Compliance:
    """Test PEP 440 compliance checking."""

    def test_check_pep440_valid_version(self):
        """Test PEP 440 compliance check for valid version."""
        # This test depends on packaging library availability
        result = check_pep440_compliance("2024.01.18.1")
        # Should not raise an error at least
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])
