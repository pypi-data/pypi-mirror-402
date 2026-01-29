"""Tests for load_config with custom configurations."""

from pathlib import Path

import pytest

from kdaquila_structure_lint.config import load_config


class TestLoadConfigCustom:
    """Tests for custom configuration loading."""

    def test_load_config_with_custom_validators(self, tmp_path: Path) -> None:
        """Should load custom validator toggles."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.structure-lint.validators]
structure = true
line_limits = false
one_per_file = false
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        assert config.validators.structure is True
        assert config.validators.line_limits is False
        assert config.validators.one_per_file is False

    def test_load_config_with_custom_search_paths(self, tmp_path: Path) -> None:
        """Should load custom search_paths at root level."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.structure-lint]
search_paths = ["src", "lib", "app"]

[tool.structure-lint.line_limits]
max_lines = 100
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        assert config.search_paths == ["src", "lib", "app"]
        assert config.line_limits.max_lines == 100

    def test_load_config_with_custom_structure(self, tmp_path: Path) -> None:
        """Should load custom structure configuration."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.structure-lint.structure]
folder_depth = 3
standard_folders = ["_types", "_helpers"]
files_allowed_anywhere = ["README.md", "NOTES.md"]
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        assert config.structure.folder_depth == 3
        assert config.structure.standard_folders == {"_types", "_helpers"}
        assert config.structure.files_allowed_anywhere == {"README.md", "NOTES.md"}

    def test_load_config_with_full_custom_config(self, tmp_path: Path) -> None:
        """Should load comprehensive custom configuration."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.structure-lint]
enabled = true
search_paths = ["src"]

[tool.structure-lint.validators]
structure = true
line_limits = true
one_per_file = false

[tool.structure-lint.line_limits]
max_lines = 200

[tool.structure-lint.structure]
folder_depth = 1
standard_folders = ["_utils"]
files_allowed_anywhere = ["README.md"]
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        # Verify all settings
        assert config.enabled is True
        assert config.search_paths == ["src"]
        assert config.validators.structure is True
        assert config.validators.line_limits is True
        assert config.validators.one_per_file is False
        assert config.line_limits.max_lines == 200
        assert config.structure.folder_depth == 1
        assert config.structure.standard_folders == {"_utils"}
        assert config.structure.files_allowed_anywhere == {"README.md"}

    def test_load_structure_files_allowed_anywhere_and_ignored(
        self, tmp_path: Path
    ) -> None:
        """Should load files_allowed_anywhere and ignored_folders from TOML."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.structure-lint.structure]
files_allowed_anywhere = ["__init__.py", "py.typed", "VERSION", "README.md"]
ignored_folders = ["__pycache__", ".venv", "build", "dist", ".egg-info"]
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        assert config.structure.files_allowed_anywhere == {
            "__init__.py",
            "py.typed",
            "VERSION",
            "README.md",
        }
        assert config.structure.ignored_folders == {
            "__pycache__",
            ".venv",
            "build",
            "dist",
            ".egg-info",
        }

    def test_standard_folders_without_underscore_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Config with non-underscore standard folders should raise ValueError."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('''
[tool.structure-lint]
enabled = true

[tool.structure-lint.structure]
standard_folders = ["_types", "models", "_functions"]
''')
        with pytest.raises(ValueError, match="Invalid standard_folders"):
            load_config(tmp_path)
