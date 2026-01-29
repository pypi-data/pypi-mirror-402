"""Validates project folder structure conventions.

Validates search_paths which have base_folders (apps, features) with structured rules.

See functions/structure modules for detailed validation logic.
"""

import sys

from kdaquila_structure_lint.config import Config
from kdaquila_structure_lint.validation._functions.validate_src_tree import validate_src_tree


def validate_structure(config: Config) -> int:
    """Run validation on all search_paths and return exit code."""
    project_root = config.project_root
    search_paths = config.search_paths
    all_errors: list[str] = []

    # Require at least one search_path
    if not search_paths:
        print("Error: search_paths is empty. At least one path is required.")
        return 1

    validated_count = 0

    # Validate each search_path
    for root_name in sorted(search_paths):
        root_path = project_root / root_name
        if not root_path.exists():
            print(f"Warning: {root_name}/ not found, skipping")
            continue

        print(f"Validating {root_name}/ tree...")
        root_errors = validate_src_tree(root_path, config)
        # Make paths relative to project root for cleaner error messages
        root_errors = [
            error.replace(str(project_root) + "\\", "").replace(str(project_root) + "/", "")
            for error in root_errors
        ]
        all_errors.extend(root_errors)
        validated_count += 1

    # Report results
    if all_errors:
        print(f"\nFound {len(all_errors)} validation error(s):\n")
        for error in all_errors:
            print(f"  - {error}")
        return 1

    if validated_count == 0:
        print("Warning: No search_paths directories found to validate")

    print("All folder structures are valid!")
    return 0


if __name__ == "__main__":
    from kdaquila_structure_lint.config import load_config

    config = load_config()
    sys.exit(validate_structure(config))
