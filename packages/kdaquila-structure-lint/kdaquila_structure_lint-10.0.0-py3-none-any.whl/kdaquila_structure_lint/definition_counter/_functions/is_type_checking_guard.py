"""Check if an If node is a TYPE_CHECKING guard."""

import ast


def is_type_checking_guard(node: ast.If) -> bool:
    """Check if an If node is a TYPE_CHECKING guard."""
    test = node.test
    # Handle: if TYPE_CHECKING:
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    # Handle: if typing.TYPE_CHECKING:
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
