"""Helper function for creating a Config object with custom settings."""

from pathlib import Path

from kdaquila_structure_lint.config import Config


def create_custom_config(tmp_path: Path) -> Config:
    """Create a Config object with custom settings.

    Args:
        tmp_path: The temporary path to use as project root.

    Returns:
        A Config object with custom validator and path settings.
    """
    return Config(
        enabled=True,
        project_root=tmp_path,
        search_paths=["src", "lib"],
        validators=Config.Validators(
            structure=True,
            line_limits=True,
            one_per_file=True,
        ),
        line_limits=Config.LineLimits(
            max_lines=100,
        ),
        one_per_file=Config.OnePerFile(),
        structure=Config.Structure(
            folder_depth=3,
            standard_folders={"_types", "_functions", "_helpers"},
            files_allowed_anywhere={"README.md", "NOTES.md"},
        ),
    )
