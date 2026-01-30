---
id: TC008
title: Case detail panel shows selected case information
priority: high
tags: [tui, case-browser, detail]
automation:
  status: automated
  test_path: tests/unit/test_tui.py::test_case_browser_shows_detail_panel
---

## Description

Verify that selecting a case in the tree view displays its full details in the detail panel.

## Given

- Case Browser is open with cases loaded
- A test case exists with preconditions, steps, and expected result

## When

1. Navigate to a case using arrow keys
2. Press `Enter` to select the case

## Then

- Detail panel shows case ID and title
- Priority is displayed with visual indicator
- Tags are displayed
- Automation status is shown (automated/manual)
- Preconditions section is rendered
- Steps section is rendered with numbered list
- Expected result section is rendered
- If automated, linked test path is shown
