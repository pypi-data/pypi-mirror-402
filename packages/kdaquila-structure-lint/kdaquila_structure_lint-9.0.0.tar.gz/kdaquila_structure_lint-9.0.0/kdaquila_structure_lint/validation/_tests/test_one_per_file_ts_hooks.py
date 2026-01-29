"""Tests for one-per-file validation with TypeScript files in _hooks folder."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_source_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestTypeScriptHooksFolder:
    """Tests for TypeScript files in _hooks folder."""

    def test_single_hook_passes(self, tmp_path: Path) -> None:
        """Should pass when TypeScript file has single hook."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_hooks").mkdir(parents=True)

        content = """import { useState, useCallback } from 'react';

export const useCounter = (initialValue: number = 0) => {
    const [count, setCount] = useState(initialValue);

    const increment = useCallback(() => {
        setCount(c => c + 1);
    }, []);

    return { count, increment };
};
"""
        create_source_file(tmp_path, "src/_hooks/useCounter.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_multiple_hooks_fails(self, tmp_path: Path) -> None:
        """Should fail when TypeScript file has multiple hooks."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_hooks").mkdir(parents=True)

        content = """import { useState } from 'react';

export const useCounter = () => {
    const [count, setCount] = useState(0);
    return { count, setCount };
};

export const useToggle = () => {
    const [value, setValue] = useState(false);
    return { value, toggle: () => setValue(v => !v) };
};
"""
        create_source_file(tmp_path, "src/_hooks/hooks.ts", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1
