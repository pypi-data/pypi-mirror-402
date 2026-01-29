"""Detect extra top-level definitions in source files."""

from pathlib import Path

from kdaquila_structure_lint.definition_counter._functions.detect_python_extra_definitions import (
    detect_python_extra_definitions,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.detect_typescript_extra_definitions import (  # noqa: E501
    detect_typescript_extra_definitions,
)


def detect_extra_definitions(file_path: Path) -> list[str] | None:
    """Detect extra top-level definitions based on file type.

    Routes to the appropriate language-specific detection function.

    Returns list of extra definition names, or None on parse error.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        return detect_python_extra_definitions(file_path)
    if suffix in {".ts", ".tsx"}:
        return detect_typescript_extra_definitions(file_path)
    return None
