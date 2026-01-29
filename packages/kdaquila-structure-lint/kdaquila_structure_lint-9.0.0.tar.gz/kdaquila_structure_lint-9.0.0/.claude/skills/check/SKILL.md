---
name: check
description: Verify and validate code changes by running all checks (ruff, mypy, pytest, structure-lint). Use to verify changes, validate code, or confirm everything passes before committing.
---

# Check

Run all development checks to verify changes before committing.

```bash
python scripts/check.py
```

This runs:
1. `ruff check .` - Linting
2. `mypy .` - Type checking
3. `pytest` - Tests
4. `structure-lint` - Project structure validation

Use this after completing any code changes to ensure everything passes.
