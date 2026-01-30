# 0005. Configurable test case section formats

Date: 2026-01-16

## Status

proposed

## Context

Different teams and contexts use different terminology for structuring test cases:

- **BDD (Behavior-Driven Development)**: Given / When / Then - common in business-facing specs
- **AAA (Arrange-Act-Assert)**: Arrange / Act / Assert - common among developers
- **Classic**: Preconditions / Steps / Expected Result - traditional test case format

Forcing a single format alienates users familiar with other conventions. Additionally, AI agents benefit from structured, predictable section names when parsing test cases as specifications.

## Decision

Test case section formats will be configurable via `pyproject.toml`:

```toml
[tool.testla]
section_format = "bdd"  # Options: "bdd", "aaa", "classic"
```

**Format definitions:**

| Format    | Section 1     | Section 2 | Section 3       |
| --------- | ------------- | --------- | --------------- |
| `bdd`     | Given         | When      | Then            |
| `aaa`     | Arrange       | Act       | Assert          |
| `classic` | Preconditions | Steps     | Expected Result |

**Behavior:**

1. `testla case new` generates templates using the configured format
2. The case loader recognizes ALL section name aliases regardless of config (for interoperability)
3. Default format is `bdd` (most widely recognized)

**Section aliases recognized by the parser:**

```python
SECTION_ALIASES = {
    "preconditions": ["given", "arrange", "preconditions", "setup", "pre-conditions"],
    "steps": ["when", "act", "steps", "action", "actions"],
    "expected": ["then", "assert", "expected", "expected result", "expected results"],
}
```

This means a team using BDD format can still read cases written in AAA format, and vice versa.

## Consequences

### Positive

- Teams can use familiar terminology
- AI agents get predictable structure (Given/When/Then is well-documented in training data)
- Interoperability: mixed formats work because parser recognizes all aliases
- BDD format aligns with industry-standard Gherkin syntax

### Negative

- Slight increase in configuration complexity
- Teams might mix formats inconsistently (mitigated by parser accepting all aliases)
