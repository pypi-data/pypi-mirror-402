# SPDX-FileCopyrightText: 2026-present QAToolist <qatoolist@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Version metadata for hatch_calvar_sample package."""

try:
    from importlib.metadata import version as get_package_version
except ImportError:
    # Python < 3.8
    from importlib_metadata import version as get_package_version

# Try to get version from package metadata (when installed)
try:
    __version__ = get_package_version("hatch-calvar-sample")
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
