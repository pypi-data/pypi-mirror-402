"""Check if a node is a function assignment."""

from tree_sitter import Node


def is_function_assignment(node: Node) -> bool:
    """Check if a variable_declarator assigns a function/arrow function."""
    for child in node.children:
        if child.type in {"arrow_function", "function_expression", "function"}:
            return True
    return False
