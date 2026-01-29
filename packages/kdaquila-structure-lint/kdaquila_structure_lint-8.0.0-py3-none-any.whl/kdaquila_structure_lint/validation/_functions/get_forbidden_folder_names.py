"""Generate forbidden folder names from standard folders."""


def get_forbidden_folder_names(standard_folders: set[str]) -> set[str]:
    """Generate forbidden folder names from standard folders.

    If standard_folders contains "_types", then "types" is forbidden.
    """
    forbidden = set()
    for folder in standard_folders:
        if folder.startswith("_"):
            forbidden.add(folder[1:])  # Remove leading underscore
    return forbidden
