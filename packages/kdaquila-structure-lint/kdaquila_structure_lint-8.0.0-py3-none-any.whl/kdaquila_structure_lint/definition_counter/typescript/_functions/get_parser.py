"""Create tree-sitter parser for TypeScript files."""

from pathlib import Path

from tree_sitter import Language, Parser
from tree_sitter_typescript import language_tsx, language_typescript


def get_parser(file_path: Path) -> Parser:
    """Create a tree-sitter parser for the appropriate TypeScript dialect."""
    parser = Parser()
    if file_path.suffix.lower() == ".tsx":
        parser.language = Language(language_tsx())
    else:
        parser.language = Language(language_typescript())
    return parser
