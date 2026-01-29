"""Extract variable name from tree-sitter nodes."""

from tree_sitter import Node


def get_variable_name(node: Node) -> str | None:
    """Extract variable name from a variable_declarator node."""
    for child in node.children:
        if child.type == "identifier":
            return child.text.decode("utf-8") if child.text else None
    return None
