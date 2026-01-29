"""Tests for forbidden folder name validation."""

from pathlib import Path

from _pytest.capture import CaptureFixture

from kdaquila_structure_lint.test_fixtures import build_structure, create_minimal_config
from kdaquila_structure_lint.validation._functions.validate_structure import validate_structure


class TestStructureValidatorForbiddenNames:
    """Tests for forbidden folder name validation."""

    def test_underscore_types_folder_passes(self, tmp_path: Path) -> None:
        """Should pass when using valid _types standard folder."""
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

    def test_types_folder_fails_with_forbidden_error(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should fail when using 'types' instead of '_types'."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "my_feature": {
                            "types": {"module.py": ""},  # Forbidden - should be _types
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Folder name 'types' is forbidden" in captured.out
        assert "use underscore prefix: _types" in captured.out

    def test_nested_functions_folder_is_caught(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should catch forbidden folder names at nested levels."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "my_feature": {
                            "sub_feature": {
                                "functions": {"module.py": ""},  # Forbidden - should be _functions
                            },
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Folder name 'functions' is forbidden" in captured.out
        assert "use underscore prefix: _functions" in captured.out

    def test_multiple_forbidden_folders_all_reported(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should report all forbidden folder violations."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "feature_a": {
                            "types": {"module.py": ""},  # Forbidden
                        },
                        "feature_b": {
                            "functions": {"module.py": ""},  # Forbidden
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        assert exit_code == 1
        # Both forbidden folders should be reported
        assert "Folder name 'types' is forbidden" in captured.out
        assert "Folder name 'functions' is forbidden" in captured.out
