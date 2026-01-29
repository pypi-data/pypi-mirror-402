"""Validates that filename matches the single definition name in standard folders.

Ensures consistent naming conventions by checking that files containing exactly
one definition have a filename that matches the definition name.
"""

from pathlib import Path

from kdaquila_structure_lint.validation._functions.should_skip_filename_match import (
    should_skip_filename_match,
)


def validate_filename_matches_definition(
    file_path: Path, definition_names: list[str]
) -> str | None:
    """Validate that filename matches the single definition name.

    Returns None if validation passes or is not applicable.
    Returns error message if filename doesn't match definition.

    Validation is skipped if:
    - File should skip filename match (barrel/init/test files)
    - File does not have exactly one definition
    - Definition name is '<default>' (anonymous export)
    """
    # Skip if file is a barrel/init/test file
    if should_skip_filename_match(file_path):
        return None

    # Skip if not exactly one definition
    if len(definition_names) != 1:
        return None

    definition_name = definition_names[0]

    # Skip anonymous exports
    if definition_name == "<default>":
        return None

    # Compare filename stem to definition name (case-sensitive)
    file_stem = file_path.stem
    if file_stem != definition_name:
        return f"filename '{file_stem}' does not match definition name '{definition_name}'"

    return None
