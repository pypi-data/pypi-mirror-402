"""Definition counter feature - counts top-level definitions in source files."""

from kdaquila_structure_lint.definition_counter._functions.count_top_level_definitions import (
    count_top_level_definitions,
)
from kdaquila_structure_lint.definition_counter._functions.detect_extra_definitions import (
    detect_extra_definitions,
)

__all__ = ["count_top_level_definitions", "detect_extra_definitions"]
