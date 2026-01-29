"""Detect extra top-level definitions in Python files."""

import ast
from pathlib import Path

from kdaquila_structure_lint.definition_counter._functions.get_assigned_names import (
    get_assigned_names,
)
from kdaquila_structure_lint.definition_counter._functions.is_dunder_name import (
    is_dunder_name,
)
from kdaquila_structure_lint.definition_counter._functions.is_main_guard import (
    is_main_guard,
)
from kdaquila_structure_lint.definition_counter._functions.is_type_checking_guard import (
    is_type_checking_guard,
)


def detect_python_extra_definitions(file_path: Path) -> list[str] | None:
    """Detect extra top-level definitions that aren't functions/classes.

    Returns list of extra definition names, or None on parse error.
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None

    extras: list[str] = []

    for node in ast.iter_child_nodes(tree):
        # Skip imports
        if isinstance(node, ast.Import | ast.ImportFrom):
            continue

        # Skip function and class definitions
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue

        # Skip TYPE_CHECKING and __name__ == "__main__" guards
        if isinstance(node, ast.If) and (is_type_checking_guard(node) or is_main_guard(node)):
            continue

        # Check assignments for extra definitions
        if isinstance(node, ast.Assign | ast.AnnAssign):
            names = get_assigned_names(node)
            for name in names:
                # Allow dunder names like __all__, __version__
                if not is_dunder_name(name):
                    extras.append(name)

    return extras
