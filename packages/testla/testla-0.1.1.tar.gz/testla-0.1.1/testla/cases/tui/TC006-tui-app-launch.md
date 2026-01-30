---
id: TC006
title: TUI application launches and displays dashboard
priority: high
tags: [tui, dashboard]
automation:
  status: automated
  test_path: tests/unit/test_tui.py::test_app_launches_with_dashboard
---

## Description

Verify that the Testla TUI launches successfully and displays the dashboard as the initial screen.

## Given

- Testla is initialized in the repository (`testla/` directory exists)
- Test cases exist in `testla/cases/`

## When

1. Run `testla tui` command

## Then

- TUI application launches without errors
- Dashboard screen is displayed as the initial view
- Project name is shown in the header
- Key bindings are displayed in the footer
- Press `q` exits the application cleanly
