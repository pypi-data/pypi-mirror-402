"""Determines whether a file should skip filename match validation.

Identifies files that are exempt from the filename-matches-definition rule,
such as barrel/init files and test files.
"""

from pathlib import Path


def should_skip_filename_match(file_path: Path) -> bool:
    """Check if file should skip filename match validation.

    Returns True for:
    - Barrel/init files: index.ts, index.tsx, __init__.py
    - Test files: *.test.ts, *.test.tsx, *.spec.ts, *.spec.tsx, test_*.py, *_test.py
    """
    file_name = file_path.name

    # Barrel/init files
    if file_name in {"index.ts", "index.tsx", "__init__.py"}:
        return True

    # TypeScript test files
    if file_name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
        return True

    # Python test files
    if file_name.startswith("test_") and file_name.endswith(".py"):
        return True

    return file_name.endswith("_test.py")
