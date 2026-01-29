"""Tests for one-per-file validation with TypeScript files in _classes folder."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_source_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestTypeScriptClassesFolder:
    """Tests for TypeScript files in _classes folder."""

    def test_single_class_passes(self, tmp_path: Path) -> None:
        """Should pass when TypeScript file has single class."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_classes").mkdir(parents=True)

        content = """export class UserService {
    private users: string[] = [];

    addUser(name: string): void {
        this.users.push(name);
    }

    getUsers(): string[] {
        return this.users;
    }
}
"""
        create_source_file(tmp_path, "src/_classes/UserService.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_multiple_classes_fails(self, tmp_path: Path) -> None:
        """Should fail when TypeScript file has multiple classes."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_classes").mkdir(parents=True)

        content = """export class UserService {
    getUser(): string {
        return 'user';
    }
}

export class ProductService {
    getProduct(): string {
        return 'product';
    }
}
"""
        create_source_file(tmp_path, "src/_classes/services.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1
