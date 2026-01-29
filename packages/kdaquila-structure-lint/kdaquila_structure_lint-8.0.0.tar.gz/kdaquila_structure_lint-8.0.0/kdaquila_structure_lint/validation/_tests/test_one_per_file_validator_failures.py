"""Tests for one-per-file validation failures."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_python_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestOnePerFileValidatorFailures:
    """Tests for failure cases in one-per-file validation."""

    def test_file_with_multiple_functions_fails(self, tmp_path: Path) -> None:
        """Should fail when file in _functions folder has multiple functions."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """def func1():
    pass

def func2():
    pass
"""
        create_python_file(tmp_path, "src/_functions/multi.py", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1

    def test_file_with_multiple_classes_fails(self, tmp_path: Path) -> None:
        """Should fail when file in _classes folder has multiple classes."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_classes").mkdir(parents=True)

        content = """class Class1:
    pass

class Class2:
    pass
"""
        create_python_file(tmp_path, "src/_classes/multi.py", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1

    def test_file_with_function_and_class_fails(self, tmp_path: Path) -> None:
        """Should fail when file in _functions folder has both function and class."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """def my_func():
    pass

class MyClass:
    pass
"""
        create_python_file(tmp_path, "src/_functions/mixed.py", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1

    def test_async_function_counted(self, tmp_path: Path) -> None:
        """Should count async functions as definitions in _functions folder."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """async def async_func():
    pass

def sync_func():
    pass
"""
        create_python_file(tmp_path, "src/_functions/async.py", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1
