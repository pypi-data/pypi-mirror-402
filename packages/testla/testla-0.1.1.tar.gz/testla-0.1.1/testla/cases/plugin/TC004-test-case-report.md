---
id: TC004
title: Testla report shows pass/fail status per case ID
priority: high
tags: [plugin, pytest, reporting]
automation:
  status: automated
  test_path: tests/unit/test_pytest_plugin.py::test_report_shows_case_results
---

## Description

Verify that after running pytest with testla markers, a summary report shows the pass/fail/skip status for each referenced case ID.

## Given

- Tests marked with @pytest.mark.testla() referencing various case IDs
- Some tests pass, some fail, some are skipped

## When

1. Run pytest on the test suite

## Then

- Report header "Testla Test Case Report" is displayed
- Each case ID is listed with its result (PASS/FAIL/SKIP)
- Multiple tests can reference the same case ID (results aggregated)
- Single test can reference multiple case IDs (each tracked separately)
- No report is shown if no testla markers are present
