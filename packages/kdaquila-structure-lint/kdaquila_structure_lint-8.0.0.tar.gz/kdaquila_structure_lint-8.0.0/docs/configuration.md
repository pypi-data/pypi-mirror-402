# Configuration Reference

This document provides a complete reference for all configuration options available in `kdaquila-structure-lint`.

## Configuration Location

Configuration is stored in your project's `pyproject.toml` file under the `[tool.structure-lint]` section:

```toml
[tool.structure-lint]
enabled = true
# ... additional configuration
```

## Configuration Loading

The configuration system uses a **deep merge** strategy:

1. Load default values for all settings
2. Search for `pyproject.toml` (or use `--config` path if provided)
3. Merge user settings with defaults
4. Any missing field uses the default value

This means you only need to specify the settings you want to change from the defaults.

## Complete Schema

### Master Switch

#### `enabled`

**Type**: `bool`
**Default**: `true`

Master switch to enable/disable the entire linter. Useful for temporarily disabling without removing configuration.

```toml
[tool.structure-lint]
enabled = false  # Disables all validation
```

### Search Paths

#### `search_paths`

**Type**: `list[str]`
**Default**: `["src"]`

List of directories to search for Python files, relative to project root. This setting applies to **all validators** - it is the unified configuration for which directories the linter should examine.

```toml
[tool.structure-lint]
search_paths = ["src", "lib", "tools"]  # Custom search paths for all validators
```

**Behavior**:
- At least one search path should be specified (empty list means no files are validated)
- Missing paths are warned and skipped (don't cause validation failure)
- Each path is validated independently using the same rules
- The tool automatically excludes common non-source directories like `.venv`, `__pycache__`, `.git`, etc.

**Example**:
```
project/
├── src/              # Validated (in search_paths)
├── lib/              # Validated (in search_paths)
├── scripts/          # Not validated (not in search_paths)
└── experiments/      # Not validated (not in search_paths)
```

### Validator Toggles

Control which validators are enabled. Each can be toggled independently.

#### `validators.structure`

**Type**: `bool`
**Default**: `false` (opt-in)

Enable the opinionated structure validator. This is disabled by default because it enforces a specific folder organization pattern.

```toml
[tool.structure-lint.validators]
structure = true  # Opt-in to structure validation
```

#### `validators.line_limits`

**Type**: `bool`
**Default**: `true`

Enable the line limits validator that enforces maximum lines per file.

```toml
[tool.structure-lint.validators]
line_limits = false  # Disable line limit checking
```

#### `validators.one_per_file`

**Type**: `bool`
**Default**: `true`

Enable the one-per-file validator that ensures single top-level definition per file.

```toml
[tool.structure-lint.validators]
one_per_file = false  # Disable one-per-file checking
```

### One-Per-File Configuration

Settings for the one-per-file validator. This validator uses folder-aware rules to apply appropriate checks based on the folder name and file type.

#### `one_per_file.ts_fun_in_functions`

**Type**: `bool`
**Default**: `true`

Enforce one function per TypeScript file in `_functions` folders.

```toml
[tool.structure-lint.one_per_file]
ts_fun_in_functions = true
```

#### `one_per_file.ts_fun_in_components`

**Type**: `bool`
**Default**: `true`

Enforce one function (React component) per TypeScript file in `_components` folders.

```toml
[tool.structure-lint.one_per_file]
ts_fun_in_components = true
```

#### `one_per_file.ts_fun_in_hooks`

**Type**: `bool`
**Default**: `true`

Enforce one function (React hook) per TypeScript file in `_hooks` folders.

```toml
[tool.structure-lint.one_per_file]
ts_fun_in_hooks = true
```

#### `one_per_file.ts_cls_in_classes`

**Type**: `bool`
**Default**: `true`

Enforce one class per TypeScript file in `_classes` folders.

```toml
[tool.structure-lint.one_per_file]
ts_cls_in_classes = true
```

#### `one_per_file.py_fun_in_functions`

**Type**: `bool`
**Default**: `true`

Enforce one function per Python file in `_functions` folders.

```toml
[tool.structure-lint.one_per_file]
py_fun_in_functions = true
```

#### `one_per_file.py_cls_in_classes`

**Type**: `bool`
**Default**: `true`

Enforce one class per Python file in `_classes` folders.

```toml
[tool.structure-lint.one_per_file]
py_cls_in_classes = true
```

#### `one_per_file.excluded_patterns`

**Type**: `list[str]`
**Default**: `["*.d.ts"]`

List of glob patterns for files to exclude from one-per-file validation. TypeScript declaration files (`.d.ts`) are excluded by default since they commonly contain multiple type definitions.

```toml
[tool.structure-lint.one_per_file]
excluded_patterns = ["*.d.ts", "*.generated.ts"]
```

### Line Limits Configuration

Settings for the line limits validator.

#### `line_limits.max_lines`

**Type**: `int`
**Default**: `150`

Maximum number of lines allowed per Python file.

```toml
[tool.structure-lint.line_limits]
max_lines = 200  # Allow up to 200 lines
```

**Rationale**: The default of 150 lines encourages modular code without being overly restrictive. Files beyond this size often indicate opportunities for refactoring.

### Structure Validation Configuration

Settings for the opinionated structure validator. Note that the structure validator uses the root-level `search_paths` setting to determine which directories to validate.

#### `structure.folder_depth`

**Type**: `int`
**Default**: `2`

Maximum nesting depth for feature folders within a base folder.

```toml
[tool.structure-lint.structure]
folder_depth = 3  # Allow deeper nesting
```

**Example with depth=2**:
```
src/features/authentication/     # depth 0 (child of base folder)
├── authentication_services/     # depth 1 (feature folder)
│   └── authentication_services_oauth/   # depth 2 (at limit)
│       └── authentication_services_oauth_providers/  # depth 3 - ERROR: exceeds limit
```

**Rationale**: Limits folder nesting to prevent overly deep hierarchies that become hard to navigate.

#### `structure.standard_folders`

**Type**: `list[str]` (converted to set internally)
**Default**: `["_types", "_functions", "_constants", "_tests", "_errors", "_classes", "_components", "_hooks"]`

List of standard folder names that can appear in feature/module directories. These represent common supporting code categories and cannot contain subdirectories.

**Note**: `_components` and `_hooks` are included by default for TypeScript/React projects.

**Important: Underscore Requirement**

All entries in `standard_folders` **must** start with an underscore (`_`). This is enforced at configuration load time. The underscore convention signals "internal organizational structure, not public interface" and distinguishes standard folders from feature folders.

```toml
# Valid configuration
[tool.structure-lint.structure]
standard_folders = ["_types", "_functions", "_constants", "_tests", "_errors", "_classes", "_components", "_hooks", "_models", "_views"]

# INVALID - will raise an error (entries must start with underscore)
standard_folders = ["_types", "models", "_functions"]  # "models" is invalid
```

Error for invalid configuration:
```
Invalid standard_folders: ['models']. All entries must start with underscore (e.g., '_models' not 'models')
```

Additionally, the validator forbids using non-underscore versions of standard folder names in your codebase. If `_types` is a standard folder, then `types/` is forbidden and flagged as a violation.

**Example Structure**:
```
src/features/authentication/
├── _types/
├── _functions/
├── _constants/
├── _tests/
├── _errors/
├── _classes/
├── _components/    # TypeScript/React components
└── _hooks/         # TypeScript/React hooks
```

#### `structure.files_allowed_anywhere`

**Type**: `list[str]` (converted to set internally)
**Default**: `["__init__.py", "index.ts", "index.tsx"]`

List of files that are allowed in any directory, even those that normally shouldn't contain files directly.

**Note**: `index.ts` and `index.tsx` are included by default for TypeScript/React projects, as they serve a similar purpose to `__init__.py` (re-exporting from a directory).

**Important**: The structure validator only validates `.py`, `.ts`, and `.tsx` files. Other files (like `README.md`, `.gitkeep`, `py.typed`, etc.) are automatically ignored and do not need to be listed here.

```toml
[tool.structure-lint.structure]
files_allowed_anywhere = ["__init__.py", "index.ts", "index.tsx", "conftest.py"]
```

**Note**: In v2.0.0, `internally_allowed_files` was merged into this setting (previously called `allowed_files`). The setting was renamed to `files_allowed_anywhere` to better reflect its purpose now that non-.py files are automatically ignored.

#### `structure.ignored_folders`

**Type**: `list[str]` (converted to set internally)
**Default**: `["__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".hypothesis", ".tox", ".coverage", "*.egg-info"]`

List of folder name patterns to ignore during structure validation. Supports wildcards (e.g., `*.egg-info` matches `my_package.egg-info`). These are typically cache, build, or tool-generated directories.

```toml
[tool.structure-lint.structure]
ignored_folders = ["__pycache__", ".mypy_cache", ".venv", "build", "dist", "*.egg-info"]
```

**Use Case**: Add project-specific build or cache directories that should not be validated.

## Common Use Cases

### Minimal Configuration

Just enable the tool with all defaults:

```toml
[tool.structure-lint]
enabled = true
```

This gives you:
- Line limits: 150 lines max
- One-per-file: enforced
- Structure: disabled

### Disable All Validators Temporarily

```toml
[tool.structure-lint]
enabled = false
```

### Increase Line Limit

```toml
[tool.structure-lint]
enabled = true

[tool.structure-lint.line_limits]
max_lines = 200
```

### Only Check Specific Directory

```toml
[tool.structure-lint]
enabled = true
search_paths = ["src"]  # Only check src/ for all validators
```

### Enable Structure Validation

```toml
[tool.structure-lint]
enabled = true
search_paths = ["src"]

[tool.structure-lint.validators]
structure = true  # Opt-in

[tool.structure-lint.structure]
standard_folders = ["_types", "_functions", "_constants", "_tests", "_errors", "_classes", "_components", "_hooks"]
folder_depth = 2
```

### Custom Project Layout

```toml
[tool.structure-lint]
enabled = true
search_paths = ["lib", "tools"]  # All validators use these paths

[tool.structure-lint.validators]
structure = true

[tool.structure-lint.line_limits]
max_lines = 200

[tool.structure-lint.structure]
standard_folders = ["_models", "_views", "_controllers", "_tests"]
folder_depth = 3
```

### Relaxed Configuration

For projects that want basic checks without strict enforcement:

```toml
[tool.structure-lint]
enabled = true
search_paths = ["src"]

[tool.structure-lint.validators]
line_limits = true
one_per_file = false  # Allow multiple definitions
structure = false

[tool.structure-lint.line_limits]
max_lines = 300  # More lenient
```

### Strict Configuration

For projects that want maximum enforcement:

```toml
[tool.structure-lint]
enabled = true
search_paths = ["src", "tests"]  # Validate both src/ and tests/

[tool.structure-lint.validators]
line_limits = true
one_per_file = true
structure = true

[tool.structure-lint.line_limits]
max_lines = 100  # Very strict

[tool.structure-lint.structure]
standard_folders = ["_types", "_functions", "_constants", "_tests", "_errors", "_classes", "_components", "_hooks"]
folder_depth = 2
files_allowed_anywhere = ["__init__.py", "index.ts", "index.tsx"]
```

## Configuration Validation

The configuration system validates your settings when loading. Common errors:

### Invalid Type

```toml
[tool.structure-lint.line_limits]
max_lines = "150"  # Error: Should be int, not string
```

### Invalid TOML Syntax

```toml
[tool.structure-lint]
enabled = true
validators.structure = true  # Error: Should use [tool.structure-lint.validators]
```

### Missing Required Parent

```toml
[tool.structure-lint.line_limits]
max_lines = 150
# Note: [tool.structure-lint] parent is optional, defaults will be used
```

## Command-Line Overrides

Some settings can be overridden via command-line arguments:

```bash
# Override project root (ignores auto-detection)
structure-lint --project-root /custom/path

# Use different config file
structure-lint --config /path/to/custom-pyproject.toml

# Enable verbose output
structure-lint --verbose
```

Note: Command-line arguments override configuration file settings.

## Environment-Specific Configuration

For different environments (dev, CI, etc.), you can maintain separate configuration files:

```bash
# Development
structure-lint --config pyproject.dev.toml

# CI (strict)
structure-lint --config pyproject.ci.toml
```

Or use the `enabled` flag to disable in specific environments:

```toml
# pyproject.toml
[tool.structure-lint]
enabled = true  # Enabled locally

# Override in CI with a script that modifies this value
```

## Tips

1. **Start Small**: Begin with just line limits and one-per-file, add structure validation later
2. **Incremental Adoption**: Use high line limits initially, gradually decrease as you refactor
3. **Team Alignment**: Discuss and agree on limits before enforcing in CI/CD
4. **Opt-In Validation**: Only directories in `search_paths` are validated - leave out directories you don't want to enforce structure on
5. **Document Choices**: Add comments in `pyproject.toml` explaining your configuration choices

## Migration from v7.x

Version 8.0.0 adds TypeScript support and folder-aware one-per-file rules. Here's what changed:

### New Configuration Section

A new `[tool.structure-lint.one_per_file]` section is available for fine-grained control:

```toml
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

### New Default Standard Folders

The `standard_folders` default now includes TypeScript/React folders:

| v7.x Default | v8.0.0 Default |
|--------------|----------------|
| `["_types", "_functions", "_constants", "_tests", "_errors", "_classes"]` | `["_types", "_functions", "_constants", "_tests", "_errors", "_classes", "_components", "_hooks"]` |

### New Default Files Allowed Anywhere

The `files_allowed_anywhere` default now includes TypeScript index files:

| v7.x Default | v8.0.0 Default |
|--------------|----------------|
| `["__init__.py"]` | `["__init__.py", "index.ts", "index.tsx"]` |

### Behavioral Changes

1. **TypeScript Support**: The linter now validates `.ts` and `.tsx` files in addition to `.py` files.

2. **Folder-Aware Rules**: One-per-file validation now uses the containing folder name to determine which rule applies. For example, files in `_functions` are checked for one function, while files in `_classes` are checked for one class.

3. **`.d.ts` Exclusion**: TypeScript declaration files are excluded by default since they commonly contain multiple type definitions.

4. **No Migration Required**: If you're upgrading from v7.x, your existing configuration will continue to work. TypeScript files will automatically be validated using the new defaults.

## Migration from v4.x

Version 5.0.0 simplifies the configuration by unifying all search path settings into a single root-level `search_paths` option. Here's how to migrate:

### Configuration Changes

| v4.x Field | v5.0.0 Field | Notes |
|------------|--------------|-------|
| `line_limits.search_paths = ["src"]` | `search_paths = ["src"]` | Moved to root level |
| `one_per_file.search_paths = ["src"]` | `search_paths = ["src"]` | Moved to root level |
| `structure.strict_format_roots = ["src"]` | `search_paths = ["src"]` | Renamed and moved to root level |

### Migration Examples

**Before (v4.x)**:
```toml
[tool.structure-lint]
enabled = true

[tool.structure-lint.validators]
structure = true

[tool.structure-lint.line_limits]
max_lines = 150
search_paths = ["src", "lib"]

[tool.structure-lint.one_per_file]
search_paths = ["src", "lib"]

[tool.structure-lint.structure]
strict_format_roots = ["src", "lib"]
standard_folders = ["types", "functions", "constants", "tests", "errors", "classes"]
```

**After (v5.0.0)**:
```toml
[tool.structure-lint]
enabled = true
search_paths = ["src", "lib"]  # Unified search paths for ALL validators

[tool.structure-lint.validators]
structure = true

[tool.structure-lint.line_limits]
max_lines = 150

[tool.structure-lint.structure]
standard_folders = ["_types", "_functions", "_constants", "_tests", "_errors", "_classes"]
```

### Behavioral Changes

1. **Unified Search Paths**: In v4.x, each validator had its own `search_paths` (or `strict_format_roots` for structure). In v5.0.0, there is a single `search_paths` at the root level that applies to all validators.

2. **Simplified Configuration**: You no longer need to specify the same paths multiple times for different validators.

3. **Consistent Behavior**: All validators now search the same directories, ensuring consistent validation across your codebase.

## Migration from v1.x

Version 2.0.0 introduced breaking changes to the structure validation configuration. Here's how to migrate (note: if migrating from v1.x directly to v5.0.0, also see the v4.x migration section above):

### Configuration Changes

| v1.x Field | v2.0.0+ Field | Notes |
|------------|---------------|-------|
| `src_root = "src"` | `search_paths = ["src"]` | Moved to root level in v5.0.0 |
| `free_form_roots = ["experiments"]` | (removed) | Just don't include in `search_paths` |
| `general_folder = "general"` | (removed) | No longer needed |
| (new) | `folder_depth = 2` | Configurable max nesting depth |

### Migration Examples

**Before (v1.x)**:
```toml
[tool.structure-lint.structure]
src_root = "src"
free_form_roots = ["experiments", "legacy"]
standard_folders = ["types", "functions", "constants", "tests", "errors", "classes"]
general_folder = "general"
```

**After (v5.0.0)**:
```toml
[tool.structure-lint]
search_paths = ["src"]  # Only validate src/
# experiments/ and legacy/ are NOT validated (not in search_paths)

[tool.structure-lint.structure]
standard_folders = ["_types", "_functions", "_constants", "_tests", "_errors", "_classes"]
folder_depth = 2
```

### Behavioral Changes

1. **Opt-in Model**: In v1.x, `src_root` was validated and `free_form_roots` were exempted. In v5.0.0, only roots listed in `search_paths` are validated. Everything else is ignored.

2. **Multiple Roots**: You can now validate multiple source directories:
   ```toml
   search_paths = ["src", "lib", "packages"]
   ```

3. **Missing Roots**: If a root in `search_paths` doesn't exist, the tool warns and continues (v1.x would fail).

4. **Depth Limits**: The `folder_depth` setting limits how deep feature folders can nest.

5. **Standard + Feature Coexistence**: Standard folders and feature folders can now coexist at the same level (previously there were mutual exclusivity rules).

## See Also

- [Validator Details](validators.md) - Detailed rules for each validator
- [Examples](examples/) - Sample configuration files
- [README](../README.md) - Main documentation
