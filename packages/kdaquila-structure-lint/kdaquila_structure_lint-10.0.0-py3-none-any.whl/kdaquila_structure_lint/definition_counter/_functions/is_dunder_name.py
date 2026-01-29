"""Check if a name is a dunder name."""


def is_dunder_name(name: str) -> bool:
    """Check if name is a dunder (e.g., __all__, __version__)."""
    return name.startswith("__") and name.endswith("__")
