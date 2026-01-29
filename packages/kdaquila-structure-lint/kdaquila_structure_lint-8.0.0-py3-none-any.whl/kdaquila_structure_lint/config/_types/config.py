"""Configuration types for structure-lint."""

from dataclasses import dataclass, field
from pathlib import Path

from kdaquila_structure_lint.config._constants import (
    DEFAULT_ENABLED,
    DEFAULT_FILES_ALLOWED_ANYWHERE,
    DEFAULT_FOLDER_DEPTH,
    DEFAULT_IGNORED_FOLDERS,
    DEFAULT_LINE_LIMITS_ENABLED,
    DEFAULT_MAX_LINES,
    DEFAULT_ONE_PER_FILE_ENABLED,
    DEFAULT_SEARCH_PATHS,
    DEFAULT_STANDARD_FOLDERS,
    DEFAULT_STRUCTURE_ENABLED,
)


@dataclass
class Config:
    """Master configuration for structure-lint."""

    @dataclass
    class Validators:
        """Control which validators are enabled."""
        structure: bool = DEFAULT_STRUCTURE_ENABLED      # Opt-in (too opinionated)
        line_limits: bool = DEFAULT_LINE_LIMITS_ENABLED  # Enabled by default
        one_per_file: bool = DEFAULT_ONE_PER_FILE_ENABLED  # Enabled by default

    @dataclass
    class LineLimits:
        """Configuration for line limits validator."""
        max_lines: int = DEFAULT_MAX_LINES

    @dataclass
    class OnePerFile:
        """Configuration for one-per-file validator."""
        # TypeScript folder-specific rules
        ts_fun_in_functions: bool = True
        ts_fun_in_components: bool = True
        ts_fun_in_hooks: bool = True
        ts_cls_in_classes: bool = True

        # Python folder-specific rules
        py_fun_in_functions: bool = True
        py_cls_in_classes: bool = True

        # Exclusion patterns (glob patterns for files to skip)
        excluded_patterns: list[str] = field(default_factory=lambda: ["*.d.ts"])

    @dataclass
    class Structure:
        """Configuration for structure validator."""
        folder_depth: int = DEFAULT_FOLDER_DEPTH
        standard_folders: set[str] = field(
            default_factory=lambda: set(DEFAULT_STANDARD_FOLDERS)
        )
        files_allowed_anywhere: set[str] = field(
            default_factory=lambda: set(DEFAULT_FILES_ALLOWED_ANYWHERE)
        )
        ignored_folders: set[str] = field(
            default_factory=lambda: set(DEFAULT_IGNORED_FOLDERS)
        )

    # Instance fields
    enabled: bool = DEFAULT_ENABLED
    project_root: Path = field(default_factory=Path.cwd)
    search_paths: list[str] = field(default_factory=lambda: list(DEFAULT_SEARCH_PATHS))
    validators: Validators = field(default_factory=Validators)
    line_limits: LineLimits = field(default_factory=LineLimits)
    one_per_file: OnePerFile = field(default_factory=OnePerFile)
    structure: Structure = field(default_factory=Structure)
