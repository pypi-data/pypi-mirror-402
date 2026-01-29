"""Validates that Python files do not exceed maximum line count.

Enforces a line limit to encourage modular, focused files.
"""

import sys

from kdaquila_structure_lint.config import Config
from kdaquila_structure_lint.validation._functions.find_source_files import find_source_files
from kdaquila_structure_lint.validation._functions.validate_file_lines import validate_file_lines


def validate_line_limits(config: Config) -> int:
    """Run validation and return exit code."""
    project_root = config.project_root
    max_lines = config.line_limits.max_lines
    search_paths = config.search_paths
    errors = []

    print(f"🔍 Checking Python files for {max_lines} line limit...\n")

    for search_path in search_paths:
        path = project_root / search_path
        if not path.exists():
            print(f"⚠️  Warning: {search_path}/ not found, skipping")
            continue

        print(f"  Scanning {search_path}/...")
        python_files = find_source_files(path, extensions={".py"})

        for file_path in python_files:
            # Make path relative to project root for cleaner error messages
            try:
                relative_path = file_path.relative_to(project_root)
            except ValueError:
                relative_path = file_path

            error = validate_file_lines(file_path, max_lines)
            if error:
                # Replace absolute path with relative path in error message
                error = error.replace(str(file_path), str(relative_path))
                errors.append(error)

    if errors:
        print(f"\n❌ Found {len(errors)} file(s) exceeding {max_lines} line limit:\n")
        for error in errors:
            print(f"  • {error}")
        print("\n💡 Consider splitting large files into smaller, focused modules.")
        return 1

    print(f"\n✅ All Python files are within {max_lines} line limit!")
    return 0


if __name__ == "__main__":
    from kdaquila_structure_lint.config import load_config

    config = load_config()
    sys.exit(validate_line_limits(config))
