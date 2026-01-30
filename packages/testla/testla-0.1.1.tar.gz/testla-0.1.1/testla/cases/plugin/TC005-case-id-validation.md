---
id: TC005
title: Unknown case IDs trigger warnings during collection
priority: medium
tags: [plugin, pytest, validation]
automation:
  status: automated
  test_path: tests/unit/test_pytest_plugin.py::test_warns_on_unknown_case_id
---

## Description

Verify that when a test references a case ID that doesn't exist in testla/cases/, a warning is emitted to alert developers of the mismatch.

## Given

- A testla/cases/ directory with known case files
- A test using @pytest.mark.testla("TC999") where TC999 doesn't exist

## When

1. Run pytest collection phase

## Then

- A warning is emitted: "Testla case 'TC999' not found in testla/cases/"
- The test still runs (warning, not error)
- Valid case IDs in the same test don't trigger warnings
