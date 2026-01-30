---
id: TC009
title: Case Browser filters cases by criteria
priority: medium
tags: [tui, case-browser, filter]
automation:
  status: none
---

## Description

Verify that the Case Browser can filter cases by various criteria like automation status, priority, and tags.

## Given

- Case Browser is open with multiple cases
- Cases have varying priorities, automation status, and tags

## When

1. Press `/` to focus the filter input
2. Enter filter criteria (e.g., `automated:yes priority:high`)
3. Press `Enter` to apply filter

## Then

- Tree view updates to show only matching cases
- Case count in header updates to reflect filtered results
- Filter criteria is displayed in the filter bar
- Pressing `Escape` clears the filter
- Folders with no matching cases are hidden
