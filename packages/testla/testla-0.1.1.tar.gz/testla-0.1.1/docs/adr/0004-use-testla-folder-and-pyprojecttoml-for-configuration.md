# 0004. Use testla folder and pyproject.toml for configuration

Date: 2026-01-16

## Status

proposed

## Context

The initial design placed test cases in `.testla/cases/` with configuration in `.testla/config.yaml`. This has several problems:

1. **Hidden directory for content**: Test cases are documents that developers and QA should see and work with regularly. Hiding them in a dotfile directory makes them less discoverable.

2. **Non-standard config location**: Python projects conventionally use `pyproject.toml` for tool configuration (ruff, mypy, pytest, etc.). A separate `.testla/config.yaml` adds another config file to manage.

3. **Inconsistent with similar tools**: Alembic uses `alembic/versions/` for migrations - a visible, purpose-named directory. This pattern is well-understood.

## Decision

**Test cases** will be stored in a visible `testla/cases/` directory:

```
myproject/
├── pyproject.toml
├── testla/
│   └── cases/
│       ├── auth/
│       │   └── TC001-login.md
│       └── checkout/
│           └── TC002-cart.md
├── src/
└── tests/
```

**Configuration** will be stored in `pyproject.toml` under the `[tool.testla]` section:

```toml
[tool.testla]
project_name = "My Project"
case_id_prefix = "TC"
case_id_digits = 3
default_priority = "medium"

[tool.testla.github]
repo = "owner/repo"
status_checks = true
```

The `testla init` command will:

1. Create `testla/cases/` directory
2. Add `[tool.testla]` section to `pyproject.toml` (or create it if missing)

## Consequences

### Positive

- **Visible content**: Test cases are no longer hidden; they appear in file explorers and `ls` output
- **Standard config**: Follows Python ecosystem conventions; one less config file
- **Familiar pattern**: Similar to `alembic/`, `migrations/`, and other tool directories
- **IDE support**: `pyproject.toml` has good editor support for TOML syntax

### Negative

- **Breaking change**: Existing projects using `.testla/` will need to migrate
- **pyproject.toml coupling**: Projects without `pyproject.toml` will need to create one (though this is rare for Python projects now)
- **Larger pyproject.toml**: Adds another `[tool.*]` section to an already busy file
