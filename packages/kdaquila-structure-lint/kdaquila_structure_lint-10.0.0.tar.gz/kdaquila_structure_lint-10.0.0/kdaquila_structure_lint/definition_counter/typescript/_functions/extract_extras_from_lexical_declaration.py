"""Extract extra definitions from lexical declarations."""

from tree_sitter import Node

from kdaquila_structure_lint.definition_counter.typescript._functions.get_variable_name import (
    get_variable_name,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.is_function_assignment import (  # noqa: E501
    is_function_assignment,
)


def extract_extras_from_lexical_declaration(node: Node) -> list[str]:
    """Extract extra definitions from lexical declarations.

    Flags const declarations that are NOT function assignments.
    Also flags let declarations (though let is typically variable_declaration, not lexical).
    """
    extras: list[str] = []

    # Check if this is a const declaration
    is_const = any(child.type == "const" for child in node.children)

    # Look for variable_declarator children
    for child in node.children:
        if child.type == "variable_declarator":
            if is_const and is_function_assignment(child):
                # const with function assignment is allowed, not an extra
                continue
            # Non-function const or let - this is an extra
            name = get_variable_name(child)
            if name:
                extras.append(name)

    return extras
