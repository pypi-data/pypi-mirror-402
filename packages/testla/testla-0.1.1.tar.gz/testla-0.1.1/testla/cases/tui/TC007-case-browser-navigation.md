---
id: TC007
title: Case Browser displays cases in tree view
priority: high
tags: [tui, case-browser]
automation:
  status: automated
  test_path: tests/unit/test_tui.py::test_case_browser_shows_tree
---

## Description

Verify that the Case Browser screen displays test cases organized in a collapsible tree structure by section path.

## Given

- Test cases exist in `testla/cases/` with various section paths
- TUI is running on the dashboard

## When

1. Press `c` to navigate to Case Browser

## Then

- Case Browser screen is displayed
- Navigation tabs show "Cases" as active
- Cases are organized in a tree by section path (e.g., `auth/login/`)
- Folders show case count (e.g., `auth/ (24)`)
- Automated cases show `●` indicator
- Manual cases show `○` indicator
- Tree is expandable/collapsible
