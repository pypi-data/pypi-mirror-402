# Testla Project Handoff

## Project Vision

Testla is a git-native FOSS test case management system inspired by "Quality Assurance in Another World". Key differentiators:

- **Repository as source of truth**: Test cases live as Markdown files in `testla/cases/`, not in a database
- **CLI-first**: Command line and TUI are primary interfaces
- **Git-native**: Cases branch, merge, have history like code
- **pytest integration**: `@pytest.mark.testla("TC001")` marker links tests to cases

## Current State

### Completed

- Domain models in `src/testla/domain/` (TestCase, TestRun, Result, Project)
- Repository layer in `src/testla/repository/` (config loading, case file parsing)
- Typer CLI in `src/testla/cli.py` with `init`, `case list`, `case show`, `case new` commands
- pytest plugin with `@pytest.mark.testla()` marker and test report
- Unit tests in `tests/unit/` (27 tests passing)
- pyproject.toml configured with uv, ruff, mypy, tox
- ADRs initialized with dark-madr in `docs/adr/`
- Configuration via `pyproject.toml` `[tool.testla]` section

### Not Yet Done

- TUI not implemented (placeholder in `src/testla/tui/`)
- API not implemented (placeholder in `src/testla/api/`)
- GitHub integration (status checks, PR comments)

## Key Files

| File                                   | Purpose                                  |
| -------------------------------------- | ---------------------------------------- |
| `src/testla/cli.py`                    | CLI entry point (Typer)                  |
| `src/testla/pytest_plugin.py`          | pytest marker and reporting              |
| `src/testla/domain/test_case.py`       | Core TestCase model                      |
| `src/testla/repository/case_loader.py` | Parses Markdown case files               |
| `src/testla/repository/config.py`      | Handles `pyproject.toml` `[tool.testla]` |
| `docs/adr/`                            | Architecture Decision Records            |
| `CLAUDE.md`                            | Project context                          |

## Project Structure

```
testla/                    # Test cases directory
  cases/
    auth/
      TC001-login.md

src/testla/                # Source code
  cli.py
  pytest_plugin.py
  domain/
  repository/
  tui/                     # Planned
  api/                     # Planned

docs/
  adr/                     # Architecture Decision Records
  design/                  # Design specs
```

## Configuration

Config lives in `pyproject.toml`:

```toml
[tool.testla]
project_name = "My Project"
case_id_prefix = "TC"
case_id_digits = 3
```

## Test Case File Format

Cases are Markdown with YAML frontmatter in `testla/cases/`:

```markdown
---
id: TC001
title: User can login with valid credentials
priority: high
tags: [auth, smoke]
automation:
  status: automated
  test_path: tests/test_auth.py::test_valid_login
---

## Preconditions

- User account exists

## Steps

1. Navigate to login page
2. Enter valid credentials

## Expected Result

User sees dashboard
```

## pytest Integration

Link tests to cases:

```python
import pytest

@pytest.mark.testla("TC001")
def test_user_can_login():
    ...
```

Run and see report:

```bash
pytest -m testla -v
```

## CLI Usage

```bash
testla init --name "My Project"    # Initialize in repo
testla case list                    # List all cases
testla case show TC001              # Show case details
testla case new auth/login          # Create new case
```

## Next Steps

1. ☐ Implement TUI with Textual
2. ☐ GitHub integration (status checks, PR comments)
3. ☐ Case generation from existing tests

## Development

```bash
uv sync --group dev          # Install dependencies
uv run pytest tests/ -v      # Run tests
uv run testla --help         # CLI help
uv run adr list              # List ADRs
```
