# 0002. Repository as source of truth for test cases

Date: 2026-01-16

## Status

proposed

## Context

Traditional test case management systems (TestRail, Zephyr, qTest) store test cases in proprietary databases. This creates several problems:

- **Disconnect from code**: Test cases live separately from the code they test, making it hard to keep them synchronized
- **No version history**: Changes to test cases are tracked in a separate system from code changes
- **No branching**: Cannot create feature branches with corresponding test case changes
- **PR reviews impossible**: Test case changes cannot be reviewed alongside code changes
- **Vendor lock-in**: Migrating between systems requires complex data exports/imports
- **CI/CD friction**: Requires API calls to external systems to fetch test definitions

## Decision

Test cases will be stored as Markdown files with YAML frontmatter in the `.testla/cases/` directory within the repository.

Example format:

```markdown
---
id: TC001
title: User can login with valid credentials
priority: high
tags: [auth, smoke]
automation:
  status: automated
  test_path: tests/test_auth.py::test_valid_login
---

## Preconditions

- User account exists

## Steps

1. Navigate to login page
2. Enter valid credentials

## Expected Result

User sees dashboard
```

The backend (API/database) stores only:

- Test runs (execution sessions)
- Results (outcomes of executing cases)
- Test case snapshots (immutable copies at execution time)

The backend does NOT store test case definitions.

## Consequences

### Positive

- **Git-native versioning**: Test cases have full git history, branches, and merges
- **PR reviewable**: Test case changes appear in pull requests alongside code
- **Code-adjacent**: Cases live next to the automated tests that implement them
- **No vendor lock-in**: Plain Markdown files are portable and tooling-agnostic
- **Offline-first**: No external service required to view/edit test cases
- **CI-native**: Cases are available in CI without API calls

### Negative

- **Git literacy required**: Users must understand git workflows to manage test cases
- **No web UI for editing**: Cannot edit test cases through a browser (without additional tooling)
- **Conflict resolution**: Merge conflicts in test cases must be resolved manually
- **Large repos**: Repositories with thousands of test cases may become unwieldy
- **Access control**: Cannot restrict test case visibility separately from code
