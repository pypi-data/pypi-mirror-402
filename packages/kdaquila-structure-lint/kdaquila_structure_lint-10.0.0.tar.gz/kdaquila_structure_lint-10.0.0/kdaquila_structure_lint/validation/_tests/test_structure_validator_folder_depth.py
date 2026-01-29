"""Tests for folder_depth configuration with depth 0 and 1."""

from pathlib import Path

from _pytest.capture import CaptureFixture

from kdaquila_structure_lint.test_fixtures import build_structure, create_minimal_config
from kdaquila_structure_lint.validation._functions.validate_structure import validate_structure


class TestFolderDepthShallow:
    """Tests for folder_depth configuration with shallow depths."""

    def test_folder_depth_0_requires_standard_at_base(self, tmp_path: Path) -> None:
        """With folder_depth=0, base folders must have standard folders only."""
        config = create_minimal_config(tmp_path)
        config.structure.folder_depth = 0

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "_types": {"module.py": ""},
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        # This should pass - base folder has standard folders
        assert exit_code == 0

    def test_folder_depth_0_rejects_nested_custom_folders(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """With folder_depth=0, nested custom folders inside first layer fail."""
        config = create_minimal_config(tmp_path)
        config.structure.folder_depth = 0

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "my_feature": {
                            # nested_feature is a CUSTOM folder inside my_feature
                            "nested_feature": {
                                "_types": {"module.py": ""},
                            },
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        # Nested custom folder "nested_feature" exceeds depth 0
        assert exit_code == 1
        assert "Exceeds max depth" in captured.out

    def test_folder_depth_1_allows_one_custom_layer(self, tmp_path: Path) -> None:
        """With folder_depth=1, one layer of custom folders is allowed."""
        config = create_minimal_config(tmp_path)
        config.structure.folder_depth = 1

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

    def test_folder_depth_1_rejects_nested_custom(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """With folder_depth=1, nested custom folders should fail."""
        config = create_minimal_config(tmp_path)
        config.structure.folder_depth = 1

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "domain": {
                            "subdomain": {
                                "_types": {"module.py": ""},
                            },
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Exceeds max depth" in captured.out
