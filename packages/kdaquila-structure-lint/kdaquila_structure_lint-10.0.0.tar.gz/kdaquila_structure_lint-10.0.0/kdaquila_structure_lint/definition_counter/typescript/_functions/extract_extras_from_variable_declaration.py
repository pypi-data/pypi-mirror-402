"""Extract extra definitions from variable declarations (let/var)."""

from tree_sitter import Node

from kdaquila_structure_lint.definition_counter.typescript._functions.get_variable_name import (
    get_variable_name,
)


def extract_extras_from_variable_declaration(node: Node) -> list[str]:
    """Extract extra definitions from variable declarations (let/var)."""
    extras: list[str] = []

    for child in node.children:
        if child.type == "variable_declarator":
            name = get_variable_name(child)
            if name:
                extras.append(name)

    return extras
