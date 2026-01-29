"""Count top-level definitions in TypeScript files."""

from pathlib import Path

from kdaquila_structure_lint.definition_counter.typescript._functions.extract_definitions_from_export_statement import (  # noqa: E501
    extract_definitions_from_export_statement,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.extract_definitions_from_lexical_declaration import (  # noqa: E501
    extract_definitions_from_lexical_declaration,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.get_parser import get_parser
from kdaquila_structure_lint.definition_counter.typescript._functions.has_function_body import (
    has_function_body,
)


def count_typescript_definitions(file_path: Path) -> tuple[int, list[str]] | None:
    """Count top-level function and class definitions in TypeScript files.

    Counts:
    - function declarations (with bodies, not overload signatures)
    - async function declarations
    - class declarations
    - abstract class declarations
    - const assignments to arrow functions or function expressions
    - export default functions/classes (named or anonymous)

    Does not count:
    - type aliases, interfaces, enums, namespaces
    - let/var assignments
    - function overload signatures (no body)
    - functions inside objects or as callbacks

    Returns (count, names) or None on error.
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

    definitions: list[str] = []
    root = tree.root_node

    # Iterate over top-level nodes only
    for node in root.children:
        if node.type == "function_declaration":
            # Regular function or async function declaration
            if has_function_body(node):
                for child in node.children:
                    if child.type == "identifier":
                        name = child.text.decode("utf-8") if child.text else None
                        if name:
                            definitions.append(name)
                        break

        elif node.type in {"class_declaration", "abstract_class_declaration"}:
            for child in node.children:
                if child.type == "type_identifier":
                    name = child.text.decode("utf-8") if child.text else None
                    if name:
                        definitions.append(name)
                    break

        elif node.type == "lexical_declaration":
            definitions.extend(extract_definitions_from_lexical_declaration(node))

        elif node.type == "export_statement":
            definitions.extend(extract_definitions_from_export_statement(node))

    return len(definitions), definitions
