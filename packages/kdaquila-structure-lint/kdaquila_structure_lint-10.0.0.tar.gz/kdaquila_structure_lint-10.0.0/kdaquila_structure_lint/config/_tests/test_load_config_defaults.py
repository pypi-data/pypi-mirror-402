"""Tests for load_config defaults and minimal configurations."""

from pathlib import Path

from kdaquila_structure_lint.config import load_config


class TestLoadConfigDefaults:
    """Tests for default configuration loading."""

    def test_load_config_with_all_defaults(self, tmp_path: Path) -> None:
        """Should use all default values when no config file exists."""
        config = load_config(project_root=tmp_path)

        assert config.enabled is True
        assert config.project_root == tmp_path
        assert config.search_paths == ["src"]
        assert config.validators.structure is False
        assert config.validators.line_limits is True
        assert config.validators.one_per_file is True
        assert config.line_limits.max_lines == 150
        assert config.structure.folder_depth == 2
        expected_folders = {
            "_types", "_functions", "_constants", "_tests", "_errors", "_classes",
            "_components", "_hooks"
        }
        assert config.structure.standard_folders == expected_folders
        assert config.structure.files_allowed_anywhere == {"__init__.py", "index.ts", "index.tsx"}
        assert config.structure.ignored_folders == {
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".hypothesis",
            ".tox",
            ".coverage",
            "*.egg-info",
        }

    def test_load_config_with_minimal_toml(self, tmp_path: Path) -> None:
        """Should merge minimal config with defaults."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.structure-lint]
enabled = false
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        assert config.enabled is False
        # All other values should be defaults
        assert config.validators.line_limits is True
        assert config.line_limits.max_lines == 150

    def test_load_config_partial_overrides(self, tmp_path: Path) -> None:
        """Should merge partial config with defaults."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.structure-lint.line_limits]
max_lines = 80
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        assert config.line_limits.max_lines == 80
        assert config.search_paths == ["src"]  # default

    def test_load_config_missing_tool_section(self, tmp_path: Path) -> None:
        """Should use defaults when [tool.structure-lint] section missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-project"
""")

        config = load_config(project_root=tmp_path, config_path=pyproject)

        # Should use all defaults
        assert config.enabled is True
        assert config.validators.line_limits is True
        assert config.line_limits.max_lines == 150

    def test_load_config_nonexistent_file_uses_defaults(self, tmp_path: Path) -> None:
        """Should use defaults when config file doesn't exist."""
        config = load_config(project_root=tmp_path)

        assert config.enabled is True
        assert config.project_root == tmp_path
