# Validator Reference

This document provides detailed information about each validator in `kdaquila-structure-lint`, including rules, rationale, examples, and customization options.

## Overview

The package includes three validators that work with both **Python** and **TypeScript** files:

1. **Line Limits Validator** - Enforces maximum lines per file (enabled by default)
2. **One-Per-File Validator** - Ensures single definition per file using folder-aware rules (enabled by default)
3. **Structure Validator** - Enforces folder organization (opt-in only)

### Supported File Types

| Language | Extensions |
|----------|------------|
| Python | `.py` |
| TypeScript | `.ts`, `.tsx` |

## Line Limits Validator

### Purpose

Enforces a maximum number of lines per file (Python and TypeScript) to encourage modular, focused code.

### Rationale

Files with hundreds of lines often:
- Violate single responsibility principle
- Are harder to test in isolation
- Create merge conflicts in version control
- Are intimidating for new contributors
- Indicate opportunities for refactoring

The default limit of 150 lines strikes a balance between being permissive enough for real-world code while encouraging good practices.

### Rules

1. Count total lines in each Python/TypeScript file (including blank lines and comments)
2. Report files exceeding `max_lines` threshold
3. Search only in configured `search_paths`
4. Automatically exclude common directories:
   - `.venv/`, `venv/`
   - `__pycache__/`
   - `.git/`, `.hg/`, `.svn/`
   - `node_modules/`

### Configuration

```toml
[tool.structure-lint]
search_paths = ["src"]  # Default - applies to all validators

[tool.structure-lint.validators]
line_limits = true  # Enable/disable

[tool.structure-lint.line_limits]
max_lines = 150  # Default
```

### Examples

#### Passing Example

File with 145 lines:

```python
# src/features/auth/login.py (145 lines)
"""User login functionality."""

from typing import Optional
from .types import User, Credentials

def authenticate_user(credentials: Credentials) -> Optional[User]:
    """Authenticate user with credentials."""
    # ... implementation (140 more lines)
    pass
```

Output:
```
All Python files are within 150 line limit!
```

#### Failing Example

File with 187 lines:

```python
# src/features/auth/user_manager.py (187 lines)
"""User management with too many responsibilities."""

class UserManager:
    def create_user(self): ...
    def update_user(self): ...
    def delete_user(self): ...
    def authenticate(self): ...
    def authorize(self): ...
    def send_email(self): ...
    def generate_report(self): ...
    # ... 180 more lines
```

Output:
```
Found 1 file(s) exceeding 150 line limit:

  src/features/auth/user_manager.py: 187 lines (exceeds 150 line limit)

Consider splitting large files into smaller, focused modules.
```

### Customization Options

#### Adjust Line Limit

For legacy projects or different conventions:

```toml
[tool.structure-lint.line_limits]
max_lines = 200  # More lenient
```

Or more strict:

```toml
[tool.structure-lint.line_limits]
max_lines = 100  # Forces very small modules
```

#### Change Search Paths

Only check specific directories:

```toml
[tool.structure-lint]
search_paths = ["src"]  # Only src/, ignore scripts/
```

Or check additional directories:

```toml
[tool.structure-lint]
search_paths = ["src", "lib", "tests"]
```

#### Disable Temporarily

```toml
[tool.structure-lint.validators]
line_limits = false
```

### Migration Strategy

For existing projects with violations:

1. **Start High**: Set `max_lines = 500` to establish baseline
2. **Track Progress**: Gradually lower limit as you refactor
3. **Incremental**: Lower by 50 lines every sprint/release
4. **Target**: Aim for 150 lines eventually

Example progression:
```toml
# Week 1: Establish baseline
max_lines = 500

# Month 1: First reduction
max_lines = 300

# Month 2: Getting closer
max_lines = 200

# Month 3: Target reached
max_lines = 150
```

---

## One-Per-File Validator

### Purpose

Ensures files contain at most one top-level function or class definition, using **folder-aware rules** to apply appropriate checks based on the folder name and file type.

### Rationale

Single-definition files provide:
- **Discoverability**: Clear file naming (file name = what it contains)
- **Predictability**: Easy to find where something is defined
- **Modularity**: Natural boundaries for code organization
- **Testability**: Easier to write focused unit tests
- **Refactoring**: Simpler to move and reorganize code

### Folder-Aware Rules

The validator determines which rule to apply based on:
1. The **folder name** containing the file (e.g., `_functions`, `_classes`, `_components`)
2. The **file type** (Python vs TypeScript)

| Folder | Python Rule | TypeScript Rule |
|--------|-------------|-----------------|
| `_functions` | 1 function | 1 function |
| `_classes` | 1 class | 1 class |
| `_components` | - | 1 function (React component) |
| `_hooks` | - | 1 function (React hook) |
| `_types` | no limit | no limit |
| `_constants` | no limit | no limit |

**Notes:**
- `_types` and `_constants` folders are exempt from one-per-file rules (they often contain multiple definitions)
- `_components` and `_hooks` only apply to TypeScript files (React patterns)
- Files in other folders are not validated by this rule

### Configuration

```toml
[tool.structure-lint]
search_paths = ["src"]  # Default - applies to all validators

[tool.structure-lint.validators]
one_per_file = true  # Enable/disable

[tool.structure-lint.one_per_file]
# TypeScript rules (all default: true)
ts_fun_in_functions = true   # Enforce 1 function per TS file in _functions
ts_fun_in_components = true  # Enforce 1 function per TS file in _components
ts_fun_in_hooks = true       # Enforce 1 function per TS file in _hooks
ts_cls_in_classes = true     # Enforce 1 class per TS file in _classes

# Python rules (all default: true)
py_fun_in_functions = true   # Enforce 1 function per PY file in _functions
py_cls_in_classes = true     # Enforce 1 class per PY file in _classes

# Exclusion patterns
excluded_patterns = ["*.d.ts"]  # Skip TypeScript declaration files
```

### Examples

#### Python Examples

**Single class in `_classes` folder (passing):**
```python
# src/features/auth/_classes/user.py
"""User model."""

from dataclasses import dataclass

MAX_USERNAME_LENGTH = 50  # Constants OK

@dataclass
class User:
    """User model."""
    username: str
    email: str

    def validate(self):  # Methods inside class OK
        """Validate user data."""
        return len(self.username) <= MAX_USERNAME_LENGTH
```

**Single function in `_functions` folder (passing):**
```python
# src/features/dates/_functions/format_date.py
"""Format dates for display."""

from datetime import datetime

DEFAULT_FORMAT = "%Y-%m-%d"  # Constants OK

def format_date(date: datetime, format: str = DEFAULT_FORMAT) -> str:
    """Format a date for display."""
    return date.strftime(format)
```

**Multiple types in `_types` folder (passing - no limit):**
```python
# src/features/auth/_types/models.py
"""Authentication types."""

from dataclasses import dataclass
from typing import Protocol

@dataclass
class User:
    username: str
    email: str

@dataclass
class Session:
    token: str
    user_id: int

class Authenticatable(Protocol):
    def authenticate(self) -> bool: ...
```

**Multiple classes in `_classes` folder (failing):**
```python
# src/features/auth/_classes/models.py  # BAD
"""Multiple models in one file."""

class User:
    pass

class Session:  # Second class - violation!
    pass
```

Output:
```
✗ src/features/auth/_classes/models.py: 2 classes (expected 1)
  - User (class)
  - Session (class)
```

#### TypeScript Examples

**Single component in `_components` folder (passing):**
```tsx
// src/features/buttons/_components/PrimaryButton.tsx
import React from 'react';

interface Props {
  label: string;
  onClick: () => void;
}

export function PrimaryButton({ label, onClick }: Props) {
  return (
    <button className="primary" onClick={onClick}>
      {label}
    </button>
  );
}
```

**Single hook in `_hooks` folder (passing):**
```tsx
// src/features/auth/_hooks/useAuth.ts
import { useState, useEffect } from 'react';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // ... auth logic
  }, []);

  return { user, loading };
}
```

**Multiple components in `_components` folder (failing):**
```tsx
// src/features/buttons/_components/buttons.tsx  # BAD
export function PrimaryButton() { /* ... */ }
export function SecondaryButton() { /* ... */ }  // Second component - violation!
```

Output:
```
✗ src/features/buttons/_components/buttons.tsx: 2 functions (expected 1)
  - PrimaryButton (function)
  - SecondaryButton (function)
```

**Better approach:**
```
src/features/buttons/_components/
├── PrimaryButton.tsx     # Only PrimaryButton
└── SecondaryButton.tsx   # Only SecondaryButton
```

### Special Cases

#### `__init__.py` and `index.ts`/`index.tsx` Files

These files are **exempt** from one-per-file rules:
- `__init__.py` - Python package initialization
- `index.ts` / `index.tsx` - TypeScript barrel exports

They commonly contain multiple re-exports:

```python
# src/features/auth/__init__.py
"""Authentication package."""

from .user import User
from .session import Session
from .login import login
from .logout import logout

__all__ = ["User", "Session", "login", "logout"]
```

```tsx
// src/features/buttons/_components/index.ts
export { PrimaryButton } from './PrimaryButton';
export { SecondaryButton } from './SecondaryButton';
export { IconButton } from './IconButton';
```

#### TypeScript Declaration Files (`.d.ts`)

Declaration files are **excluded by default** since they commonly contain multiple type definitions:

```typescript
// src/types/api.d.ts - automatically excluded
interface User { ... }
interface Session { ... }
interface Token { ... }
```

You can customize exclusion patterns:
```toml
[tool.structure-lint.one_per_file]
excluded_patterns = ["*.d.ts", "*.generated.ts"]
```

### Customization Options

#### Disable Specific Rules

```toml
[tool.structure-lint.one_per_file]
# Allow multiple functions in _functions folders for TypeScript
ts_fun_in_functions = false

# But still enforce for Python
py_fun_in_functions = true
```

#### Change Search Paths

```toml
[tool.structure-lint]
search_paths = ["src"]  # Only check src/ (applies to all validators)
```

#### Disable Entirely

```toml
[tool.structure-lint.validators]
one_per_file = false
```

### Migration Strategy

For projects with violations:

1. **Identify**: Run validator to find all violations
2. **Prioritize**: Start with files that have 2-3 definitions (easier wins)
3. **Refactor**: Split files and update imports
4. **Test**: Ensure tests still pass after splitting
5. **Repeat**: Tackle larger files

Example refactoring (Python):

**Before:**
```python
# src/features/utils/_functions/string_helpers.py (3 definitions)
def capitalize_words(s): ...
def snake_to_camel(s): ...
def truncate_string(s, length): ...
```

**After:**
```
src/features/utils/_functions/
├── capitalize_words.py    # capitalize_words
├── snake_to_camel.py      # snake_to_camel
└── truncate_string.py     # truncate_string
```

Example refactoring (TypeScript):

**Before:**
```tsx
// src/features/buttons/_components/Buttons.tsx (3 components)
export function PrimaryButton() { ... }
export function SecondaryButton() { ... }
export function IconButton() { ... }
```

**After:**
```
src/features/buttons/_components/
├── PrimaryButton.tsx
├── SecondaryButton.tsx
├── IconButton.tsx
└── index.ts  # Re-exports all components
```

---

## Structure Validator (Opt-in)

### Purpose

Enforces an opinionated folder structure based on feature-driven development and screaming architecture principles.

### Rationale

Consistent structure provides:
- **Navigability**: Predictable location for code
- **Scalability**: Clear patterns for adding features
- **Onboarding**: New developers know where things go
- **Separation**: Clear boundaries between features/modules

**Note**: This is **opt-in by default** because it's highly opinionated. Only enable if your team agrees to this structure.

### Underscore Convention

The structure validator enforces a naming convention where all standard folders must begin with an underscore (e.g., `_types`, `_functions`). This convention serves an important purpose:

**Why Underscore?**

The underscore prefix signals "internal organizational structure, not public interface." It visually distinguishes structural/organizational folders from feature folders, making it immediately clear which folders represent code categories vs. domain concepts.

**Two-Layer Enforcement**

1. **Configuration Validation**: All entries in `standard_folders` must start with `_`. Invalid configuration raises an error at startup:

   ```toml
   # INVALID - will raise an error
   [tool.structure-lint.structure]
   standard_folders = ["_types", "models", "_functions"]  # "models" is invalid
   ```

   Error message:
   ```
   Invalid standard_folders: ['models']. All entries must start with underscore (e.g., '_models' not 'models')
   ```

2. **Folder Validation**: Using non-underscore versions of standard folder names in your codebase is forbidden. If `_types` is configured as a standard folder, then a folder named `types/` is a violation:

   ```
   src/features/auth/
   └── types/           # ERROR: should be _types/
       └── user.py
   ```

   Error message:
   ```
   src/features/auth/types: Folder name 'types' is forbidden (use underscore prefix: _types)
   ```

**Example**

If your configuration has `standard_folders = ["_types", "_functions"]`:

- `_types/` - Valid (standard folder)
- `_functions/` - Valid (standard folder)
- `types/` - Invalid (use `_types` instead)
- `functions/` - Invalid (use `_functions` instead)
- `services/` - Valid (custom feature folder, not a standard folder name)

### The Two Rules

The structure validator enforces two simple rules:

#### Rule 1: Standard Folders Cannot Have Subdirectories

Standard folders (like `_types/`, `_functions/`, `_constants/`, `_tests/`, `_errors/`, `_classes/`, `_components/`, `_hooks/`) are leaf nodes in your folder tree. They contain source files directly but cannot contain subdirectories.

**Valid:**
```
auth/
├── _types/
│   ├── user.py
│   └── session.py
└── _functions/
    └── hash_password.py
```

**Invalid:**
```
auth/
└── _types/
    └── models/        # ERROR: subdirectory in standard folder
        └── user.py
```

#### Rule 2: Only Certain Files Allowed Outside Standard Folders

Python files can only appear in standard folders or in the `files_allowed_anywhere` list (default: `["__init__.py"]`). This prevents loose files from cluttering feature directories.

**Valid:**
```
auth/
├── __init__.py              # Allowed everywhere
├── _types/
│   └── user.py              # In standard folder
└── _functions/
    └── hash.py              # In standard folder
```

**Invalid:**
```
auth/
├── __init__.py
├── login.py                 # ERROR: not in standard folder
└── _types/
    └── user.py
```

### Configuration

```toml
[tool.structure-lint]
search_paths = ["src"]  # Roots to validate (applies to all validators)

[tool.structure-lint.validators]
structure = true  # Must opt-in explicitly

[tool.structure-lint.structure]
folder_depth = 2               # Max nesting depth for feature folders
standard_folders = ["_types", "_functions", "_constants", "_tests", "_errors", "_classes", "_components", "_hooks"]
files_allowed_anywhere = ["__init__.py", "index.ts", "index.tsx"]
ignored_folders = ["__pycache__", ".mypy_cache", "*.egg-info"]
```

### Examples

#### Valid Structure

```
project/
├── src/
│   └── features/
│       ├── authentication/
│       │   ├── __init__.py
│       │   ├── _types/
│       │   │   └── user.py
│       │   ├── _functions/
│       │   │   └── hash_password.py
│       │   ├── _constants/
│       │   │   └── config.py
│       │   ├── _tests/
│       │   │   └── test_login.py
│       │   ├── _components/             # React components (TypeScript)
│       │   │   └── LoginForm.tsx
│       │   ├── _hooks/                  # React hooks (TypeScript)
│       │   │   └── useAuth.ts
│       │   └── oauth/                   # Feature folder (nested)
│       │       ├── _types/
│       │       │   └── token.py
│       │       └── google/              # Nested feature folder
│       │           └── _types/
│       │               └── credentials.py
│       └── reporting/
│           ├── _types/
│           └── _functions/
```

#### Invalid Examples

**Files outside standard folders:**
```
src/features/auth/
├── login.py          # ERROR: Files not allowed here
└── _types/
```

Error: `src/features/auth/: Disallowed files: ['login.py']`

**Subdirectory in standard folder:**
```
src/features/auth/
└── _types/
    └── models/       # ERROR: Standard folders cannot have subdirectories
```

Error: `src/features/auth/_types: Standard folder cannot have subdirectories`

**Exceeding depth limit:**
```
src/features/auth/           # depth 0
└── services/                # depth 1
    └── oauth/               # depth 2 (at limit with default folder_depth=2)
        └── providers/       # ERROR: depth 3, exceeds limit
```

Error: `src/features/auth/services/oauth/providers: Exceeds max depth of 2`

### Standard and Feature Folders Can Coexist

Unlike previous versions, standard folders and feature folders can now exist at the same level. This provides flexibility in organizing code:

```
src/features/auth/
├── _types/                  # Standard folder
│   └── user.py
├── _functions/              # Standard folder
│   └── helper.py
├── oauth/                   # Feature folder (nested)
│   └── _types/
│       └── token.py
└── password/                # Feature folder (nested)
    └── _functions/
        └── hasher.py
```

### Customization Options

#### Different Standard Folders

```toml
[tool.structure-lint.structure]
standard_folders = ["_models", "_views", "_controllers", "_tests"]
```

Enables MVC-style organization:
```
src/features/authentication/
├── _models/
├── _views/
├── _controllers/
└── _tests/
```

**Note**: All standard folder names must start with underscore. See [Underscore Convention](#underscore-convention) above.

#### Multiple Roots

```toml
[tool.structure-lint]
search_paths = ["src", "lib", "packages"]
```

```
project_root/
├── src/          # Validated
├── lib/          # Validated
├── packages/     # Validated
└── scripts/      # Not validated (not in search_paths)
```

#### Adjusting Depth Limits

```toml
[tool.structure-lint.structure]
folder_depth = 3  # Allow deeper nesting (default is 2)
```

#### Ignored Folders

```toml
[tool.structure-lint.structure]
ignored_folders = ["__pycache__", ".mypy_cache", ".venv", "build", "dist", "*.egg-info"]
```

Add project-specific build or cache directories that should not be validated.

### Migration Strategy

Adopting the structure validator for existing projects:

#### 1. Assess Current State

Run with structure validation enabled to see violations:

```bash
structure-lint --verbose
```

#### 2. Choose Approach

**Option A: Gradual Migration**
- Start with only new directories in `search_paths`
- Apply structure to new features only
- Gradually add more directories as you refactor

```toml
[tool.structure-lint]
search_paths = ["src/new_features"]  # Only validate new code
```

**Option B: Full Reorganization**
- Plan complete restructure
- Create new structure alongside old
- Migrate in phases
- Update imports
- Run tests continuously

#### 3. Customize to Fit

Don't fight the tool - customize it:

```toml
[tool.structure-lint.structure]
# Match your team's conventions (all names must start with underscore)
standard_folders = ["_types", "_models", "_services", "_functions", "_tests", "_errors", "_classes"]
folder_depth = 3  # Allow deeper nesting if needed
```

#### 4. Document Decisions

Add comments to your config explaining choices:

```toml
[tool.structure-lint]
# Only validate src/ - legacy/ and experiments/ are excluded
search_paths = ["src"]

[tool.structure-lint.structure]
# Added "_services" as standard folder for our microservice architecture
standard_folders = ["_types", "_functions", "_constants", "_tests", "_errors", "_classes", "_services"]
```

### When to Use Structure Validation

**Use when**:
- Starting a new project
- Team agrees on structure conventions
- Project is growing and needs organization
- Onboarding new developers frequently

**Don't use when**:
- Small projects (< 5 files)
- Exploratory/prototype phase
- Team hasn't agreed on structure
- Legacy project with different conventions

---

## Common Questions

### Can I disable validators temporarily?

Yes, use the `enabled` master switch:

```toml
[tool.structure-lint]
enabled = false  # Disables everything
```

Or disable individual validators:

```toml
[tool.structure-lint.validators]
line_limits = false
one_per_file = false
structure = false
```

### Can I exclude specific files or folders?

Currently, validators skip these directories automatically:
- `.venv/`, `venv/`
- `__pycache__/`
- `.git/`, `.hg/`, `.svn/`
- `node_modules/`

For structure validation, use `ignored_folders`:

```toml
[tool.structure-lint.structure]
ignored_folders = ["__pycache__", ".mypy_cache", "build", "dist"]
```

For more specific exclusions, adjust `search_paths`:

```toml
[tool.structure-lint]
search_paths = ["src"]  # Doesn't check scripts/
```

### What if I disagree with the defaults?

All rules are configurable! Adjust to fit your team:

```toml
[tool.structure-lint.line_limits]
max_lines = 300  # Your choice

[tool.structure-lint.validators]
one_per_file = false  # Disable if not relevant
```

### How do I run only one validator?

Disable the others:

```toml
[tool.structure-lint.validators]
line_limits = true    # Only this enabled
one_per_file = false
structure = false
```

---

## See Also

- [Configuration Reference](configuration.md) - All configuration options
- [Examples](examples/) - Sample configurations
- [README](../README.md) - Main documentation
