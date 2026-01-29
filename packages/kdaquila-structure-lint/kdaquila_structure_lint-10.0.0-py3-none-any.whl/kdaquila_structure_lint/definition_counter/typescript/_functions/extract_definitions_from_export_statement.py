"""Extract definitions from export statements."""

from tree_sitter import Node

from kdaquila_structure_lint.definition_counter.typescript._functions.extract_definitions_from_lexical_declaration import (  # noqa: E501
    extract_definitions_from_lexical_declaration,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.has_function_body import (
    has_function_body,
)


def extract_definitions_from_export_statement(node: Node) -> list[str]:
    """Extract definitions from export statements.

    Handles:
    - export default function() {}
    - export default function name() {}
    - export default () => {}
    - export default class {}
    - export default class Name {}
    - export function name() {}
    - export class Name {}
    """
    definitions: list[str] = []

    is_default = any(child.type == "default" for child in node.children)

    for child in node.children:
        if child.type == "function_declaration":
            if has_function_body(child):
                name = None
                for subchild in child.children:
                    if subchild.type == "identifier":
                        name = subchild.text.decode("utf-8") if subchild.text else None
                        break
                definitions.append(name if name else "<default>")

        elif child.type in {"class_declaration", "abstract_class_declaration"}:
            name = None
            for subchild in child.children:
                if subchild.type == "type_identifier":
                    name = subchild.text.decode("utf-8") if subchild.text else None
                    break
            definitions.append(name if name else "<default>")

        elif child.type in {"arrow_function", "function_expression", "function"} and is_default:
            # export default () => {} or export default function() {}
            definitions.append("<default>")

        elif child.type == "class" and is_default:
            # export default class {}
            definitions.append("<default>")

        elif child.type == "lexical_declaration":
            # export const foo = () => {}
            definitions.extend(extract_definitions_from_lexical_declaration(child))

    return definitions
