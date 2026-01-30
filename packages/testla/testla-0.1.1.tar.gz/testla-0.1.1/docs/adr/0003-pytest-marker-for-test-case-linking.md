# 0003. Pytest marker for test case linking

Date: 2026-01-16

## Status

proposed

## Context

Teams adopting Testla may have existing automated tests (pytest) alongside test case documentation in `.testla/cases/`. We need a mechanism to:

1. **Link** automated tests to their corresponding test case documentation
2. **Validate** that referenced case IDs exist
3. **Report** traceability (which cases are automated, which are manual-only)
4. **Track** test results per case ID

Several linking mechanisms were considered:

- **Custom decorator**: `@testla("TC001")` - requires import, not pytest-native
- **Docstring convention**: `"""Testla: TC001"""` - fragile, not discoverable
- **Naming convention**: `test_TC001_login` - pollutes test names
- **External mapping file**: `.testla/mapping.yaml` - separate file to maintain
- **Pytest marker**: `@pytest.mark.testla("TC001")` - native, discoverable, filterable

## Decision

Use pytest markers to link automated tests to test case IDs:

```python
import pytest

@pytest.mark.testla("TC001")
def test_user_can_login():
    ...

# Multiple cases covered by one test
@pytest.mark.testla("TC001", "TC002")
def test_login_and_redirect():
    ...

# Combines with other markers
@pytest.mark.testla("TC001")
@pytest.mark.smoke
def test_login_smoke():
    ...
```

The pytest plugin will be bundled in the main `testla` package (monorepo) rather than a separate `pytest-testla` package because:

- The plugin needs tight coupling to `testla.repository` for case file parsing
- Coordinated versioning avoids compatibility issues
- Simpler installation: `pip install testla` includes everything
- Can always extract later if needed

The plugin registers via entry point:

```toml
[project.entry-points.pytest11]
testla = "testla.pytest_plugin"
```

## Consequences

### Positive

- **Pytest-native**: No additional imports, familiar pattern for pytest users
- **Filterable**: `pytest -m testla` runs only linked tests
- **Discoverable**: Markers are visible in `pytest --markers`
- **Validates at collection**: Missing case IDs caught before tests run
- **Enables reporting**: Plugin can generate traceability reports
- **Zero config**: Plugin auto-discovers `.testla/` in project root

### Negative

- **Marker required**: Tests without `@pytest.mark.testla` won't appear in traceability reports
- **Manual linking**: Developers must add markers; no auto-detection from test names
- **Monorepo coupling**: Plugin updates require testla release (but this is also a benefit for consistency)
