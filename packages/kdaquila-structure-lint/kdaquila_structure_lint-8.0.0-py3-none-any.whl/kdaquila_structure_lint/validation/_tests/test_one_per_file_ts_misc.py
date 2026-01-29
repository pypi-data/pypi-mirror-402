"""Tests for one-per-file validation with TypeScript _types folder, exclusions, and edge cases."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_python_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestTypeScriptTypesFolder:
    """Tests for TypeScript files in _types folder."""

    def test_types_folder_not_validated(self, tmp_path: Path) -> None:
        """Should not validate _types folder (allows any number of definitions)."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_types").mkdir(parents=True)

        # Multiple type definitions and even functions should be allowed in _types
        content = """export interface User {
    id: number;
    name: string;
}

export interface Product {
    id: number;
    price: number;
}

export type UserId = number;
export type ProductId = string;

export function isUser(obj: unknown): obj is User {
    return typeof obj === 'object' && obj !== null && 'id' in obj && 'name' in obj;
}

export function isProduct(obj: unknown): obj is Product {
    return typeof obj === 'object' && obj !== null && 'id' in obj && 'price' in obj;
}
"""
        create_python_file(tmp_path, "src/_types/models.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0


class TestTypeScriptExclusions:
    """Tests for TypeScript file exclusions."""

    def test_declaration_files_excluded(self, tmp_path: Path) -> None:
        """Should exclude .d.ts declaration files from validation."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        # Declaration files can have multiple declarations
        content = """declare function functionOne(): void;
declare function functionTwo(): void;
declare class ClassOne {}
declare class ClassTwo {}
"""
        create_python_file(tmp_path, "src/_functions/types.d.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_files_outside_standard_folders_not_validated(self, tmp_path: Path) -> None:
        """Should not validate TypeScript files outside standard folders."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "utils").mkdir(parents=True)

        # Multiple functions in non-standard folder should be allowed
        content = """export function helper1(): void {
    console.log('helper1');
}

export function helper2(): void {
    console.log('helper2');
}
"""
        create_python_file(tmp_path, "src/utils/helpers.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0


class TestTypeScriptEdgeCases:
    """Tests for TypeScript edge cases."""

    def test_let_var_assignments_not_counted(self, tmp_path: Path) -> None:
        """Should not count let/var function assignments as definitions."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_functions").mkdir(parents=True)

        content = """// let and var assignments should not be counted
let mutableFunction = () => {
    return 'mutable';
};

var oldStyleFunction = function() {
    return 'old style';
};

// Only this const should be counted
export const mainFunction = (): string => {
    return 'main';
};
"""
        create_python_file(tmp_path, "src/_functions/mainFunction.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0
