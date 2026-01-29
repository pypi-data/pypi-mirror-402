"""Helper function for creating a minimal Config object with defaults."""

from pathlib import Path

from kdaquila_structure_lint.config import Config


def create_minimal_config(tmp_path: Path) -> Config:
    """Create a minimal Config object with all defaults.

    Args:
        tmp_path: The temporary path to use as project root.

    Returns:
        A Config object with default settings.
    """
    return Config(
        enabled=True,
        project_root=tmp_path,
        search_paths=["src"],
        validators=Config.Validators(),
        line_limits=Config.LineLimits(),
        one_per_file=Config.OnePerFile(),
        structure=Config.Structure(),
    )
