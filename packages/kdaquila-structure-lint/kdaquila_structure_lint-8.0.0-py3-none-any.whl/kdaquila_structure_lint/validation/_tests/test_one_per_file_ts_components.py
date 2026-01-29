"""Tests for one-per-file validation with TypeScript files in _components folder."""

from pathlib import Path

from kdaquila_structure_lint.test_fixtures import create_minimal_config, create_python_file
from kdaquila_structure_lint.validation._functions.validate_one_per_file import (
    validate_one_per_file,
)


class TestTypeScriptComponentsFolder:
    """Tests for TypeScript files in _components folder."""

    def test_single_component_passes(self, tmp_path: Path) -> None:
        """Should pass when TSX file has single component."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_components").mkdir(parents=True)

        content = """import React from 'react';

interface ButtonProps {
    label: string;
    onClick: () => void;
}

export const Button = ({ label, onClick }: ButtonProps) => {
    return <button onClick={onClick}>{label}</button>;
};
"""
        create_python_file(tmp_path, "src/_components/Button.tsx", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 0

    def test_multiple_components_fails(self, tmp_path: Path) -> None:
        """Should fail when TSX file has multiple components."""
        config = create_minimal_config(tmp_path)
        (config.project_root / "src" / "_components").mkdir(parents=True)

        content = """import React from 'react';

export const Header = () => {
    return <header>Header</header>;
};

export const Footer = () => {
    return <footer>Footer</footer>;
};
"""
        create_python_file(tmp_path, "src/_components/layout.tsx", content)

        exit_code = validate_one_per_file(config)
        assert exit_code == 1
