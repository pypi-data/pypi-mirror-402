"""Tests for config dataclass defaults."""

from kdaquila_structure_lint.config import Config


class TestConfigDataclasses:
    """Tests for config dataclass defaults."""

    def test_validator_toggles_defaults(self) -> None:
        """Should have correct default values."""
        toggles = Config.Validators()
        assert toggles.structure is False
        assert toggles.line_limits is True
        assert toggles.one_per_file is True

    def test_line_limits_config_defaults(self) -> None:
        """Should have correct default values."""
        config = Config.LineLimits()
        assert config.max_lines == 150

    def test_structure_config_defaults(self) -> None:
        """Should have correct default values."""
        config = Config.Structure()
        assert config.folder_depth == 2
        expected_folders = {
            "_types", "_functions", "_constants", "_tests", "_errors", "_classes",
            "_components", "_hooks"
        }
        assert config.standard_folders == expected_folders
        assert config.files_allowed_anywhere == {"__init__.py", "index.ts", "index.tsx"}
        assert config.ignored_folders == {
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".hypothesis",
            ".tox",
            ".coverage",
            "*.egg-info",
        }
