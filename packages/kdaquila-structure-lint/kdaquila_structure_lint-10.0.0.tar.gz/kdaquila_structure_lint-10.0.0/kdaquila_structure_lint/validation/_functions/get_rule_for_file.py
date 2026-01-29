"""Determines which one-per-file rule applies to a given source file.

Maps files to their applicable validation rules based on the standard folder
they belong to and the file's language (Python or TypeScript).
"""

from pathlib import Path

from kdaquila_structure_lint.config import Config


def get_rule_for_file(file_path: Path, folder: str | None, config: Config) -> bool | None:
    """
    Get the applicable rule for a file based on its folder and language.

    Returns True if rule is enabled, False if disabled, None if no rule applies.
    """
    if folder is None:
        return None  # File not in a standard folder - no validation

    lang = "ts" if file_path.suffix in {".ts", ".tsx"} else "py"

    # Map folder to rule
    rule_map = {
        ("ts", "_functions"): config.one_per_file.ts_fun_in_functions,
        ("ts", "_components"): config.one_per_file.ts_fun_in_components,
        ("ts", "_hooks"): config.one_per_file.ts_fun_in_hooks,
        ("ts", "_classes"): config.one_per_file.ts_cls_in_classes,
        ("py", "_functions"): config.one_per_file.py_fun_in_functions,
        ("py", "_classes"): config.one_per_file.py_cls_in_classes,
    }

    return rule_map.get((lang, folder))  # Returns None for _types, _constants, etc.
