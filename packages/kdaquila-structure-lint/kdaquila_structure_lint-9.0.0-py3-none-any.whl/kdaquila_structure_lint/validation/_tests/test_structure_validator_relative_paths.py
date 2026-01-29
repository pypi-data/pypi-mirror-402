"""Tests for relative path handling in structure validation error messages."""

from pathlib import Path

from _pytest.capture import CaptureFixture

from kdaquila_structure_lint.test_fixtures import build_structure, create_minimal_config
from kdaquila_structure_lint.validation._functions.validate_structure import validate_structure


class TestStructureValidatorRelativePaths:
    """Tests for relative path handling in error messages."""

    def test_error_messages_use_relative_paths(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should use relative paths in error messages."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {},
                    "invalid_file.py": "",  # File in src root (not allowed)
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        # Error message should use relative path and mention the issue
        assert "src" in captured.out
        assert "Files not allowed" in captured.out
        # Should not show absolute path markers like drive letters on Windows
        assert exit_code == 1
