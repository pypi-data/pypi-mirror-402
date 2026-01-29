"""Tests for nested functions and classes in one-per-file validation."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_python_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestOnePerFileValidatorNested:
    """Tests for nested functions and classes."""

    def test_nested_functions_not_counted(self, tmp_path: Path) -> None:
        """Should not count nested functions as separate definitions in _functions folder."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """def outer():
    def inner():
        pass
    return inner
"""
        create_python_file(tmp_path, "src/_functions/outer.py", content)

        # Only one top-level definition (outer)
        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_nested_classes_not_counted(self, tmp_path: Path) -> None:
        """Should not count nested classes as separate definitions in _classes folder."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_classes").mkdir(parents=True)

        content = """class Outer:
    class Inner:
        pass
"""
        create_python_file(tmp_path, "src/_classes/Outer.py", content)

        # Only one top-level definition (Outer)
        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_class_methods_not_counted(self, tmp_path: Path) -> None:
        """Should not count class methods as separate definitions in _classes folder."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_classes").mkdir(parents=True)

        content = """class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass

    async def method3(self):
        pass
"""
        create_python_file(tmp_path, "src/_classes/MyClass.py", content)

        # Only one top-level definition (MyClass)
        exit_code = validate_one_per_file(config)
        assert exit_code == 0
