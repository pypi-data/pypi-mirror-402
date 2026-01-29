"""Tests for basic structure validation functionality."""

from pathlib import Path

from _pytest.capture import CaptureFixture

from kdaquila_structure_lint.test_fixtures import build_structure, create_minimal_config
from kdaquila_structure_lint.validation._functions.validate_structure import validate_structure


class TestStructureValidatorBasic:
    """Basic tests for validate_structure function."""

    def test_missing_strict_format_root_warns_and_skips(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should warn and skip when a strict_format_root doesn't exist."""
        config = create_minimal_config(tmp_path)
        # Default strict_format_roots is {"src"}, but src/ doesn't exist

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        # Should warn about missing root
        assert "Warning" in captured.out
        assert "not found" in captured.out
        # Still passes since no directories were actually validated
        assert exit_code == 0

    def test_valid_minimal_structure_passes(self, tmp_path: Path) -> None:
        """Should pass with valid minimal structure."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "my_feature": {
                            "_types": {"module.py": ""},
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        assert exit_code == 0

    def test_files_in_src_root_fails(self, tmp_path: Path) -> None:
        """Should fail when files exist in src root."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {},
                    "module.py": "",  # File in src root (not allowed)
                },
            },
        )

        exit_code = validate_structure(config)
        assert exit_code == 1

    def test_files_in_base_folder_fails(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should fail when files exist directly in base folders like features/."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "calculator.py": "",  # Files directly in features/ (not allowed)
                        "validator.py": "",
                        "process_data.py": "",
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Disallowed files" in captured.out
        assert "calculator.py" in captured.out

    def test_multiple_base_folders_accepted(self, tmp_path: Path) -> None:
        """Multiple base folders in src/ should be accepted with valid content."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "__init__.py": "",
                        "my_module": {
                            "_types": {"module.py": ""},
                        },
                    },
                    "apps": {
                        "__init__.py": "",
                        "my_module": {
                            "_types": {"module.py": ""},
                        },
                    },
                    "libs": {
                        "__init__.py": "",
                        "my_module": {
                            "_types": {"module.py": ""},
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)

        # Should pass - all base folders have valid structure
        assert exit_code == 0
