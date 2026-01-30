---
id: TC010
title: Dashboard displays case statistics
priority: medium
tags: [tui, dashboard, stats]
automation:
  status: automated
  test_path: tests/unit/test_tui.py::test_dashboard_shows_stats
---

## Description

Verify that the Dashboard displays accurate statistics about test cases in the repository.

## Given

- Testla is initialized with test cases
- Some cases are automated, some are manual

## When

1. Launch TUI with `testla tui`

## Then

- Quick Stats panel shows:
  - Total case count
  - Automated case count
  - Cases with linked tests
- Coverage panel shows:
  - Automated percentage with progress bar
  - Manual percentage with progress bar
- Statistics update when cases are added/removed (after refresh)
