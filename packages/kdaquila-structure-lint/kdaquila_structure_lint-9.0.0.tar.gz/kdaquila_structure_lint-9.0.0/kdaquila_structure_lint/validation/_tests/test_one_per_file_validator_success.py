"""Tests for one-per-file validation successes."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_source_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestOnePerFileValidatorSuccess:
    """Tests for success cases in one-per-file validation."""

    def test_files_with_single_definition_pass(self, tmp_path: Path) -> None:
        """Should pass when files in standard folders have single definition."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)
        (config.project_root / "src" / "_classes").mkdir(parents=True)

        # Create files with single definitions in standard folders
        create_source_file(tmp_path, "src/_functions/hello.py", "def hello():\n    pass\n")
        create_source_file(tmp_path, "src/_classes/MyClass.py", "class MyClass:\n    pass\n")

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_empty_file_passes(self, tmp_path: Path) -> None:
        """Should pass for empty files in _functions folder (0 definitions)."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        create_source_file(tmp_path, "src/_functions/empty.py", "")

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_file_with_only_imports_passes(self, tmp_path: Path) -> None:
        """Should pass for files with only imports in _functions folder."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """import os
import sys
from pathlib import Path
from collections.abc import Callable
from features.config import Config
"""
        create_source_file(tmp_path, "src/_functions/imports.py", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_file_with_constants_and_function_passes(self, tmp_path: Path) -> None:
        """Should pass when file in _functions has constants plus one function."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """MAX_SIZE = 100
DEFAULT_NAME = "test"

def process():
    pass
"""
        create_source_file(tmp_path, "src/_functions/process.py", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0
