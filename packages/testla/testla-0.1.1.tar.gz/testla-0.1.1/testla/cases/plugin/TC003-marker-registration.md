---
id: TC003
title: pytest marker is registered without warnings
priority: high
tags: [plugin, pytest]
automation:
  status: automated
  test_path: tests/unit/test_pytest_plugin.py::test_marker_is_registered
---

## Description

Verify that the @pytest.mark.testla() marker is properly registered so pytest doesn't emit "unknown marker" warnings.

## Given

- pytest is configured to load the testla plugin
- A test file using @pytest.mark.testla("TC001")

## When

1. Run pytest --strict-markers on a test with @pytest.mark.testla
2. Run pytest -W error to treat warnings as errors

## Then

- No PytestUnknownMarkWarning is raised
- Tests with testla markers execute normally
- Marker accepts one or more case IDs as arguments
