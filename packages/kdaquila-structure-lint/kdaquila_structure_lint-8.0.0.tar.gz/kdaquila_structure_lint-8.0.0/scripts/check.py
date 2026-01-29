"""Run all checks: ruff, mypy, pytest, and structure-lint."""

import subprocess
import sys


def run(cmd: str) -> bool:
    """Run a command and return True if it succeeded."""
    print(f"\n{'=' * 60}")
    print(f"Running: {cmd}")
    print("=" * 60)
    result = subprocess.run(cmd, shell=True, check=False)
    return result.returncode == 0


def main() -> int:
    """Run all checks and return exit code."""
    checks = [
        "uv run ruff check .",
        "uv run mypy .",
        "uv run structure-lint",
        "uv run pytest",
    ]

    failed = []
    for cmd in checks:
        if not run(cmd):
            failed.append(cmd)

    print(f"\n{'=' * 60}")
    if failed:
        print("FAILED:")
        for cmd in failed:
            print(f"  - {cmd}")
        return 1

    print("All checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
