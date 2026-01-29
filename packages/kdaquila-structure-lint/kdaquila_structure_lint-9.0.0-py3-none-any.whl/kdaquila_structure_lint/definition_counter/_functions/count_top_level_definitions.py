"""Route to appropriate parser based on file extension."""

from pathlib import Path

from kdaquila_structure_lint.definition_counter._functions.count_python_definitions import (
    count_python_definitions,
)


def count_top_level_definitions(file_path: Path) -> tuple[int, list[str]] | None:
    """Route to appropriate parser based on file extension.

    Returns (count, names) or None on error/unsupported file type.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        return count_python_definitions(file_path)
    if suffix in {".ts", ".tsx"}:
        from kdaquila_structure_lint.definition_counter.typescript import (  # noqa: PLC0415
            count_typescript_definitions,
        )

        return count_typescript_definitions(file_path)
    return None
