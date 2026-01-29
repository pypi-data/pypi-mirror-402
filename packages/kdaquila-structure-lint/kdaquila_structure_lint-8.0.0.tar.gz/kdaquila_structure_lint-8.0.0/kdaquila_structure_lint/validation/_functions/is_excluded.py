"""Handles file exclusion patterns for one-per-file validation.

Provides pattern matching to exclude certain files from validation based on
configurable glob patterns.
"""

from fnmatch import fnmatch
from pathlib import Path


def is_excluded(file_path: Path, excluded_patterns: list[str]) -> bool:
    """Check if file matches any excluded pattern."""
    file_name = file_path.name
    return any(fnmatch(file_name, pattern) for pattern in excluded_patterns)
