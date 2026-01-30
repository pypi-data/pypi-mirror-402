---
id: TC011
title: Edit case opens file in external editor
priority: medium
tags: [tui, case-browser, edit]
automation:
  status: none
---

## Description

Verify that pressing the edit key opens the case file in the user's configured editor.

## Given

- Case Browser is open with a case selected
- `$EDITOR` environment variable is set

## When

1. Select a case in the Case Browser
2. Press `e` to edit

## Then

- TUI suspends and opens the case file in `$EDITOR`
- Editor opens at the case file path
- After closing editor, TUI resumes
- Any changes made in editor are reflected when case is reloaded
