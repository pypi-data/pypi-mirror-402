"""Finds source files recursively."""

from pathlib import Path

from kdaquila_structure_lint.config._constants.defaults import DEFAULT_SUPPORTED_EXTENSIONS

EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    ".venv", "venv", "node_modules", "__pycache__",
    "dist", "build", ".next", "coverage", ".turbo"
}


def find_source_files(root: Path, extensions: set[str] | None = None) -> list[Path]:
    """Find all source files in root, excluding common non-source directories."""
    if extensions is None:
        extensions = set(DEFAULT_SUPPORTED_EXTENSIONS)
    source_files = []
    for ext in extensions:
        for file in root.rglob(f"*{ext}"):
            if any(part in EXCLUDE_DIRS for part in file.parts):
                continue
            source_files.append(file)
    return sorted(source_files, key=lambda p: p.stat().st_mtime, reverse=True)
