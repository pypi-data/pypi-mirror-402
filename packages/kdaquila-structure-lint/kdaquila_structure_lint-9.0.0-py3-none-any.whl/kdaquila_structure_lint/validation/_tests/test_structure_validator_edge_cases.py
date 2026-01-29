"""Tests for edge cases and special scenarios in structure validation."""

from pathlib import Path

from _pytest.capture import CaptureFixture

from kdaquila_structure_lint.test_fixtures import build_structure, create_minimal_config
from kdaquila_structure_lint.validation._functions.validate_structure import validate_structure


class TestStructureValidatorEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_pycache_ignored_in_src_root(self, tmp_path: Path) -> None:
        """Should ignore __pycache__ directories."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "__pycache__": {},  # Should be ignored
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

    def test_multiple_structure_violations_all_reported(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should report all violations, not just first one."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "base1": {},  # Base folders (automatically accepted)
                    "base2": {},
                    "file1.py": "",  # Files directly in root - not allowed
                    "file2.py": "",
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        # Should report files not allowed in root
        assert "Files not allowed" in captured.out or "file1.py" in captured.out
        assert exit_code == 1

    def test_empty_src_directory_passes(self, tmp_path: Path) -> None:
        """Should pass when src directory is empty (no base folders yet)."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {},  # Empty src directory
            },
        )

        exit_code = validate_structure(config)
        # Empty src is valid - allows gradual project setup
        assert exit_code == 0

    def test_complex_valid_structure(self, tmp_path: Path) -> None:
        """Should pass with complex but valid structure."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "auth": {
                            "_types": {"auth_types.py": ""},
                            "_functions": {"auth_functions.py": ""},
                        },
                        "users": {
                            "_types": {"users_types.py": ""},
                            "_functions": {"users_functions.py": ""},
                        },
                        "posts": {
                            "_types": {"posts_types.py": ""},
                            "_functions": {"posts_functions.py": ""},
                        },
                    },
                },
                "scripts": {
                    "build": {"run.py": ""},
                    "test": {"run.py": ""},
                    "deploy": {"run.py": ""},
                },
            },
        )

        exit_code = validate_structure(config)
        assert exit_code == 0

    def test_egg_info_ignored(self, tmp_path: Path) -> None:
        """Should ignore .egg-info directories without causing validation errors."""
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
                    "my_package.egg-info": {  # Should be ignored via wildcard pattern
                        "PKG-INFO": "",
                        "SOURCES.txt": "",
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        assert exit_code == 0
