"""Detects which standard folder contains a given file."""

from pathlib import Path


def get_standard_folder(file_path: Path, standard_folders: set[str]) -> str | None:
    """
    Find the innermost standard folder containing this file.

    Traverses the file path from innermost to outermost directory
    to find the first standard folder that contains the file.

    Args:
        file_path: Path to the file
        standard_folders: Set of folder names considered "standard" (e.g., {"_functions", "_types"})

    Returns:
        The name of the standard folder (e.g., "_functions") if found, or None if the file
        is not inside any standard folder.

    Examples:
        >>> get_standard_folder(Path("src/auth/_functions/login.py"), {"_functions", "_types"})
        "_functions"
        >>> get_standard_folder(Path("src/auth/helpers.py"), {"_functions", "_types"})
        None
        >>> get_standard_folder(
        ...     Path("src/_types/models/_functions/foo.py"), {"_functions", "_types"}
        ... )
        "_functions"  # Returns innermost match
    """
    for part in reversed(file_path.parts):
        if part in standard_folders:
            return part
    return None
