# Testla

Git-native test case management for modern development workflows.

## What is Testla?

Testla stores test cases as Markdown files in your repository, making them:

- **Version controlled** - Cases branch, merge, and have history like code
- **PR reviewable** - Test case changes appear alongside code changes
- **CI-native** - No external service required to access test definitions

## Quick Start

```bash
# Install
pip install testla

# Initialize in your repo
testla init --name "My Project"

# Create a test case
testla case new auth/login --title "User can login"

# List cases
testla case list
```

## Test Case Format

Cases live in `testla/cases/` as Markdown with YAML frontmatter:

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

Link automated tests to cases using the `@pytest.mark.testla` marker:

```python
import pytest

@pytest.mark.testla("TC001")
def test_user_can_login():
    ...
```

Run tests and see the Testla report:

```bash
pytest -m testla -v
```

## Configuration

Add to your `pyproject.toml`:

```toml
[tool.testla]
project_name = "My Project"
case_id_prefix = "TC"
case_id_digits = 3
```

## Development

```bash
# Clone and install
git clone https://github.com/m1yag1/testla.git
cd testla
uv sync --group dev

# Run tests
uv run pytest tests/ -v

# Format and lint
uv run ruff format .
uv run ruff check .
```

## License

Apache-2.0
