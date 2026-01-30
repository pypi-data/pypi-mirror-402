---
id: TC001
title: Case can be created with required and optional fields
priority: high
tags: [domain, case]
automation:
  status: automated
  test_path: tests/unit/test_domain_case.py::test_case_creation
---

## Description

Verify that the Case domain model can be instantiated correctly with both minimal required fields and full optional metadata.

## Given

- The Case dataclass is available from testla.domain.case

## When

1. Create a Case with only required fields (id, external_id, title)
2. Create a Case with automation metadata linking to a test path
3. Create a Case with full metadata (priority, tags, custom fields)

## Then

- Minimal case has default values for optional fields
- Automated case correctly reports is_automated as True
- Full metadata case preserves all provided values
