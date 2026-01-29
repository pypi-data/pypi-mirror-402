"""Validates custom folder structure."""

from pathlib import Path

from kdaquila_structure_lint.config import Config
from kdaquila_structure_lint.validation._functions.get_forbidden_folder_names import (
    get_forbidden_folder_names,
)
from kdaquila_structure_lint.validation._functions.matches_any_pattern import matches_any_pattern


def validate_custom_folder(path: Path, config: Config, depth: int) -> list[str]:
    """Validate custom folder in structured base.

    This function validates folders according to two rules:
    1. Standard folders cannot contain subdirectories
    2. Only certain files are allowed outside standard folders

    Args:
        path: The folder path to validate.
        config: The configuration object.
        depth: Current depth level (0 = direct child of base folder).

    Returns:
        List of error messages, empty if validation passes.
    """
    errors: list[str] = []

    # If this folder itself is a standard folder, validate it as such and return early
    if path.name in config.structure.standard_folders:
        subdirs = [
            c
            for c in path.iterdir()
            if c.is_dir()
            and not matches_any_pattern(c.name, config.structure.ignored_folders)
        ]
        if subdirs:
            errors.append(f"{path}: Standard folder cannot have subdirectories")
        return errors

    # Check if this folder uses a forbidden name (non-underscore version of standard folder)
    forbidden_names = get_forbidden_folder_names(config.structure.standard_folders)
    if path.name in forbidden_names:
        errors.append(
            f"{path}: Folder name '{path.name}' is forbidden (use underscore prefix: _{path.name})"
        )
        return errors

    # Check disallowed files (Rule 3) - only applies to feature folders
    py_files = [c.name for c in path.iterdir() if c.is_file() and c.suffix == ".py"]
    disallowed = [f for f in py_files if f not in config.structure.files_allowed_anywhere]
    if disallowed:
        errors.append(f"{path}: Disallowed files: {disallowed}")

    # Get children (excluding ignored folders)
    children = [
        c
        for c in path.iterdir()
        if c.is_dir() and not matches_any_pattern(c.name, config.structure.ignored_folders)
    ]

    # Validate each child
    for child in children:
        if child.name in config.structure.standard_folders:
            # Standard folder: validate no subdirs (Rule 1)
            subdirs = [
                c
                for c in child.iterdir()
                if c.is_dir()
                and not matches_any_pattern(c.name, config.structure.ignored_folders)
            ]
            if subdirs:
                errors.append(f"{child}: Standard folder cannot have subdirectories")
        elif child.name in forbidden_names:
            # Forbidden folder name (non-underscore version of standard folder)
            errors.append(
                f"{child}: Folder name '{child.name}' is forbidden "
                f"(use underscore prefix: _{child.name})"
            )
        # Feature folder
        # Check depth limit
        elif depth >= config.structure.folder_depth:
            errors.append(
                f"{child}: Exceeds max depth of {config.structure.folder_depth}"
            )
        else:
            errors.extend(validate_custom_folder(child, config, depth + 1))

    return errors
