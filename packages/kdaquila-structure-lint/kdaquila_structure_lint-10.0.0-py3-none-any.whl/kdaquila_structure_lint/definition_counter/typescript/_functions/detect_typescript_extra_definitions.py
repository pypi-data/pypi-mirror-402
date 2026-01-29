"""Detect extra top-level definitions that aren't functions/classes in TypeScript files."""

from pathlib import Path

from kdaquila_structure_lint.definition_counter.typescript._functions.extract_extras_from_export_statement import (  # noqa: E501
    extract_extras_from_export_statement,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.extract_extras_from_lexical_declaration import (  # noqa: E501
    extract_extras_from_lexical_declaration,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.extract_extras_from_variable_declaration import (  # noqa: E501
    extract_extras_from_variable_declaration,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.get_declaration_name import (
    get_declaration_name,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.get_parser import get_parser


def detect_typescript_extra_definitions(file_path: Path) -> list[str] | None:
    """Detect extra top-level definitions that aren't functions/classes.

    Flags as "extra":
    - type aliases (type Foo = ...)
    - interfaces (interface Foo { ... })
    - enums (enum Foo { ... })
    - const declarations that are NOT function assignments
    - let/var declarations
    - Exported versions of all the above

    Allows (not flagged):
    - Import statements
    - Declare statements (ambient_declaration)
    - Function declarations
    - Class declarations (including abstract)
    - const assignments to arrow functions or function expressions
    - Export statements that export functions/classes
    - Re-exports (export { Foo } from './foo')

    Returns list of extra definition names, or None on parse error.
    """
    try:
        content = file_path.read_bytes()
    except OSError:
        return None

    try:
        parser = get_parser(file_path)
        tree = parser.parse(content)
    except Exception:
        return None

    extras: list[str] = []
    root = tree.root_node

    for node in root.children:
        if node.type in {"type_alias_declaration", "interface_declaration"}:
            name = get_declaration_name(node, "type_identifier")
            if name:
                extras.append(name)

        elif node.type == "enum_declaration":
            name = get_declaration_name(node, "identifier")
            if name:
                extras.append(name)

        elif node.type == "lexical_declaration":
            extras.extend(extract_extras_from_lexical_declaration(node))

        elif node.type == "variable_declaration":
            extras.extend(extract_extras_from_variable_declaration(node))

        elif node.type == "export_statement":
            extras.extend(extract_extras_from_export_statement(node))

    return extras
