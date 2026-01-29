#!/usr/bin/env python3
"""Calculate next CalVer version (YYYY.MM.DD.MICRO) from git tags."""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from typing import List, Optional, Tuple

CALVER_PATTERN = re.compile(
    r"^v?(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})\.(?P<micro>\d+)$"
)


def parse_calver_tag(tag: str) -> Optional[Tuple[int, int, int, int]]:
    """Parse a CalVer tag string into (year, month, day, micro).

    Supports both 'vYYYY.MM.DD.MICRO' and 'YYYY.MM.DD.MICRO' formats.

    Args:
        tag: Git tag string

    Returns:
        Tuple of (year, month, day, micro) or None if invalid
    """
    match = CALVER_PATTERN.match(tag.strip())
    if not match:
        return None

    try:
        year = int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        micro = int(match.group("micro"))

        # Basic validation
        if not (1 <= month <= 12):
            return None
        if not (1 <= day <= 31):
            return None
        if micro < 1:
            return None

        return (year, month, day, micro)
    except (ValueError, AttributeError):
        return None


def get_git_tags() -> List[str]:
    """Fetch and return all git tags.

    Returns:
        List of tag strings (without 'v' prefix if present)
    """
    try:
        # Fetch tags from remote (if available)
        subprocess.run(["git", "fetch", "--tags"], capture_output=True, check=False)

        # Get all tags
        result = subprocess.run(
            ["git", "tag"], capture_output=True, text=True, check=True
        )
        return [tag.strip() for tag in result.stdout.splitlines() if tag.strip()]
    except subprocess.CalledProcessError:
        return []
    except FileNotFoundError:
        # Git not available
        return []


def get_current_date() -> Tuple[int, int, int]:
    """Get current UTC date as (year, month, day).

    Returns:
        Tuple of (year, month, day) in UTC
    """
    now = datetime.utcnow()
    return (now.year, now.month, now.day)


def calculate_next_version() -> str:
    """Calculate next CalVer version based on git tags and current date.

    Returns:
        Version string in format 'YYYY.MM.DD.MICRO'
    """
    current_date = get_current_date()
    year, month, day = current_date
    date_prefix = f"{year:04d}.{month:02d}.{day:02d}"

    # Get all tags and filter for CalVer format
    tags = get_git_tags()
    calver_tags = []

    for tag in tags:
        parsed = parse_calver_tag(tag)
        if parsed:
            calver_tags.append(parsed)

    # Filter tags for current date
    same_date_tags = [
        (y, m, d, micro) for y, m, d, micro in calver_tags if (y, m, d) == current_date
    ]

    # Calculate next MICRO number
    if same_date_tags:
        max_micro = max(micro for _, _, _, micro in same_date_tags)
        next_micro = max_micro + 1
    else:
        next_micro = 1

    version = f"{date_prefix}.{next_micro}"
    return version


def validate_version_format(version: str) -> bool:
    """Validate CalVer version format.

    Args:
        version: Version string to validate

    Returns:
        True if valid, False otherwise
    """
    return parse_calver_tag(version) is not None


def check_pep440_compliance(version: str) -> bool:
    """Check if version is PEP 440 compliant.

    CalVer format YYYY.MM.DD.MICRO is PEP 440 compliant as a release segment.

    Args:
        version: Version string to check

    Returns:
        True if PEP 440 compliant, False otherwise
    """
    if not validate_version_format(version):
        return False

    # Basic PEP 440 check: version should be valid
    # CalVer YYYY.MM.DD.MICRO format is valid for release segments
    try:
        from packaging import version as pkg_version

        # Just try to parse it - if it works, it's PEP 440 compliant
        pkg_version.Version(version)
        return True
    except ImportError:
        # packaging not available, assume valid if format is correct
        return validate_version_format(version)
    except Exception:
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate next CalVer version (YYYY.MM.DD.MICRO)"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate calculated version format"
    )
    parser.add_argument(
        "--pep440", action="store_true", help="Check PEP 440 compliance"
    )
    args = parser.parse_args()

    try:
        version = calculate_next_version()
    except Exception as e:
        print(f"Error calculating version: {e}", file=sys.stderr)
        return 1

    if args.validate:
        if not validate_version_format(version):
            print(f"Invalid version format: {version}", file=sys.stderr)
            return 1

    if args.pep440:
        if not check_pep440_compliance(version):
            print(f"Version not PEP 440 compliant: {version}", file=sys.stderr)
            return 1

    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
