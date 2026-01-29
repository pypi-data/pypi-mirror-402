"""Tests for one-per-file validation with TypeScript files in _functions folder."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_source_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestTypeScriptFunctionsFolder:
    """Tests for TypeScript files in _functions folder."""

    def test_single_named_function_passes(self, tmp_path: Path) -> None:
        """Should pass when TypeScript file has single named function."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """export function calculateSum(a: number, b: number): number {
    return a + b;
}
"""
        create_source_file(tmp_path, "src/_functions/calculateSum.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_single_arrow_function_passes(self, tmp_path: Path) -> None:
        """Should pass when TypeScript file has single arrow function."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """export const formatDate = (date: Date): string => {
    return date.toISOString();
};
"""
        create_source_file(tmp_path, "src/_functions/formatDate.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_multiple_functions_fails(self, tmp_path: Path) -> None:
        """Should fail when TypeScript file has multiple functions."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """export function add(a: number, b: number): number {
    return a + b;
}

export function subtract(a: number, b: number): number {
    return a - b;
}
"""
        create_source_file(tmp_path, "src/_functions/math.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1

    def test_types_not_counted(self, tmp_path: Path) -> None:
        """Should not count interfaces, types, or enums as definitions."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """interface UserInput {
    name: string;
    email: string;
}

type UserResponse = {
    id: number;
    user: UserInput;
};

enum Status {
    Active = 'active',
    Inactive = 'inactive'
}

export function processUser(input: UserInput): UserResponse {
    return { id: 1, user: input };
}
"""
        create_source_file(tmp_path, "src/_functions/processUser.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0
