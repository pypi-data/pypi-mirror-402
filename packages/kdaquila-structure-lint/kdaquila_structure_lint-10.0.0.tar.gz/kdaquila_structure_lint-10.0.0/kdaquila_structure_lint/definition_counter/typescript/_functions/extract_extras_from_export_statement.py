"""Extract extra definitions from export statements."""

from tree_sitter import Node

from kdaquila_structure_lint.definition_counter.typescript._functions.extract_extras_from_lexical_declaration import (  # noqa: E501
    extract_extras_from_lexical_declaration,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.extract_extras_from_variable_declaration import (  # noqa: E501
    extract_extras_from_variable_declaration,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.get_declaration_name import (
    get_declaration_name,
)


def extract_extras_from_export_statement(node: Node) -> list[str]:
    """Extract extra definitions from export statements.

    Flags exported type aliases, interfaces, enums, and non-function const/let/var.
    Does NOT flag exported functions/classes or re-exports.
    """
    extras: list[str] = []

    for child in node.children:
        if child.type in {"type_alias_declaration", "interface_declaration"}:
            name = get_declaration_name(child, "type_identifier")
            if name:
                extras.append(name)

        elif child.type == "enum_declaration":
            name = get_declaration_name(child, "identifier")
            if name:
                extras.append(name)

        elif child.type == "lexical_declaration":
            extras.extend(extract_extras_from_lexical_declaration(child))

        elif child.type == "variable_declaration":
            extras.extend(extract_extras_from_variable_declaration(child))

    return extras
