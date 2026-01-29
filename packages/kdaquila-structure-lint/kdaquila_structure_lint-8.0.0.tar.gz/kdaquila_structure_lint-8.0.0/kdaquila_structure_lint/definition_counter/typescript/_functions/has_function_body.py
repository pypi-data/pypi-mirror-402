"""Check if a function has a body."""

from tree_sitter import Node


def has_function_body(node: Node) -> bool:
    """Check if a function declaration has a body (not just an overload signature)."""
    return any(child.type == "statement_block" for child in node.children)
