"""TypeScript definition counter sub-feature."""

from kdaquila_structure_lint.definition_counter.typescript._functions.count_typescript_definitions import (  # noqa: E501
    count_typescript_definitions,
)
from kdaquila_structure_lint.definition_counter.typescript._functions.detect_typescript_extra_definitions import (  # noqa: E501
    detect_typescript_extra_definitions,
)

__all__ = ["count_typescript_definitions", "detect_typescript_extra_definitions"]
