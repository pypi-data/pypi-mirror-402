"""Get name from a declaration node."""

from tree_sitter import Node


def get_declaration_name(node: Node, name_type: str) -> str | None:
    """Get the name from a declaration node."""
    for child in node.children:
        if child.type == name_type:
            return child.text.decode("utf-8") if child.text else None
    return None
