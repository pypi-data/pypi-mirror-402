"""Default configuration values for structure-lint."""

# Validators defaults
DEFAULT_STRUCTURE_ENABLED = False  # Opt-in (too opinionated)
DEFAULT_LINE_LIMITS_ENABLED = True
DEFAULT_ONE_PER_FILE_ENABLED = True

# LineLimits defaults
DEFAULT_MAX_LINES = 150

# Structure defaults
DEFAULT_FOLDER_DEPTH = 2
DEFAULT_STANDARD_FOLDERS = frozenset({
    "_types", "_functions", "_constants", "_tests", "_errors", "_classes",
    "_components", "_hooks"
})
DEFAULT_FILES_ALLOWED_ANYWHERE = frozenset({"__init__.py", "index.ts", "index.tsx"})
DEFAULT_IGNORED_FOLDERS = frozenset({
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".hypothesis", ".tox", ".coverage", "*.egg-info",
})

# Config defaults
DEFAULT_ENABLED = True
DEFAULT_SEARCH_PATHS = ["src"]
