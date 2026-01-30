---
id: TC012
title: Create new case from Case Browser
priority: medium
tags: [tui, case-browser, create]
automation:
  status: none
---

## Description

Verify that pressing `n` in the Case Browser opens a modal to create a new test case, then opens it in the user's editor.

## Given

- Case Browser is open
- A section folder is selected (optional)
- `$EDITOR` environment variable is set

## When

1. Press `n` to create new case
2. Enter a title in the modal (e.g., "User can reset password")
3. Press Enter or click Create

## Then

- New case file is created with next available ID (e.g., TC012)
- File is created in the selected section folder, or root if none selected
- Filename follows pattern: `{ID}-{slugified-title}.md`
- TUI suspends and opens file in `$EDITOR`
- After closing editor, TUI resumes and tree is refreshed
- New case appears in the tree view
