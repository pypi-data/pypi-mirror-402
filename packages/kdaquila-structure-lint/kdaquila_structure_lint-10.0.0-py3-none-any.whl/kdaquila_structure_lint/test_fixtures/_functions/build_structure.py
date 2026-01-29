"""Helper function for building folder structures from nested dictionaries."""

from pathlib import Path
from typing import Any


def build_structure(base_path: Path, structure: dict[str, Any]) -> Path:
    """Build a folder structure from a nested dictionary.

    Args:
        base_path: Root directory to build structure in.
        structure: Nested dict where:
            - Keys are folder/file names
            - Dict values = folders (recurse)
            - String values = file contents
            - Empty dict {} = empty folder

    Returns:
        The base_path with structure created.

    Example:
        structure = {
            "src": {
                "features": {
                    "auth": {
                        "constants": {},
                        "utils": {"helper.py": "# helper code"},
                    },
                },
            },
        }
        build_structure(tmp_path, structure)
    """
    for name, value in structure.items():
        path = base_path / name
        if isinstance(value, dict):
            path.mkdir(parents=True, exist_ok=True)
            build_structure(path, value)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
    return base_path
