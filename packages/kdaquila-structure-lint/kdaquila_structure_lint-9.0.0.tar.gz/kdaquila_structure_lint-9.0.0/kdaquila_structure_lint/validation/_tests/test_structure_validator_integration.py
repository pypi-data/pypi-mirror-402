"""Integration tests for structure validation combining multiple aspects."""

from pathlib import Path

from _pytest.capture import CaptureFixture

from kdaquila_structure_lint.test_fixtures import (
    build_structure,
    create_custom_config,
    create_minimal_config,
)
from kdaquila_structure_lint.validation._functions.validate_structure import validate_structure


class TestStructureValidatorIntegration:
    """Integration tests combining multiple aspects."""

    def test_full_custom_config_valid_structure(self, tmp_path: Path) -> None:
        """Should validate with fully custom configuration."""
        config = create_custom_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "lib": {
                    "apps": {
                        "my_apps": {
                            "_types": {"module.py": ""},
                            "_functions": {"module.py": ""},
                            "_helpers": {"module.py": ""},
                        },
                    },
                    "features": {
                        "my_features": {
                            "_types": {"module.py": ""},
                            "_functions": {"module.py": ""},
                            "_helpers": {"module.py": ""},
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        assert exit_code == 0

    def test_structure_validation_output_format(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        """Should produce clear output format."""
        config = create_minimal_config(tmp_path)

        build_structure(
            tmp_path,
            {
                "src": {
                    "features": {
                        "my_feature": {
                            "_types": {"module.py": ""},
                        },
                    },
                },
            },
        )

        exit_code = validate_structure(config)
        captured = capsys.readouterr()

        # Should have clear progress messages
        assert "Validating" in captured.out or "src" in captured.out
        assert "valid" in captured.out.lower() or "passed" in captured.out.lower()
        assert exit_code == 0
