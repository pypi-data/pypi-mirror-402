"""Validates that source files contain at most one top-level function or class.

Encourages focused, single-responsibility modules. Applies folder-aware rules
based on which standard folder the file is in.
"""

import sys

from kdaquila_structure_lint.config import Config
from kdaquila_structure_lint.validation._functions._validate_file import _validate_file
from kdaquila_structure_lint.validation._functions.find_source_files import find_source_files


def validate_one_per_file(config: Config) -> int:
    """Run validation and return exit code."""
    project_root = config.project_root
    search_paths = config.search_paths
    errors: list[str] = []
    name_errors: list[str] = []

    print("🔍 Checking for one function/class per file...\n")

    for search_path in search_paths:
        path = project_root / search_path
        if not path.exists():
            print(f"⚠️  Warning: {search_path}/ not found, skipping")
            continue

        print(f"  Scanning {search_path}/...")
        source_files = find_source_files(path)

        for file_path in source_files:
            _validate_file(file_path, config, errors, name_errors)

    errors_found = False

    if errors:
        errors_found = True
        print(f"\n❌ Found {len(errors)} file(s) with multiple definitions:\n")
        for error in errors:
            print(f"  • {error}")
        print("\n💡 Consider splitting into separate files for better modularity.")

    if name_errors:
        errors_found = True
        print(f"\n❌ Found {len(name_errors)} file(s) with mismatched filenames:\n")
        for error in name_errors:
            print(f"  • {error}")
        print("\n💡 Rename the file to match the definition, or vice versa.")

    if errors_found:
        return 1

    print("\n✅ All files have at most one top-level function or class!")
    return 0


if __name__ == "__main__":
    from kdaquila_structure_lint.config import load_config

    config = load_config()
    sys.exit(validate_one_per_file(config))
