"""Counts and validates lines in files.

This module re-exports everything from the line_counter modules for backward compatibility.
"""

from kdaquila_structure_lint.validation._functions.count_file_lines import count_file_lines
from kdaquila_structure_lint.validation._functions.validate_file_lines import validate_file_lines

__all__ = [
    "count_file_lines",
    "validate_file_lines",
]
