---
id: TC002
title: Run follows correct state machine lifecycle
priority: high
tags: [domain, run]
automation:
  status: automated
  test_path: tests/unit/test_domain_models.py::test_run_lifecycle
---

## Description

Verify that Run correctly manages state transitions from PENDING through RUNNING to COMPLETED/CANCELLED.

## Given

- A Run in PENDING status

## When

1. Call start() on a pending run
2. Call complete() on a running run
3. Alternatively, call cancel() on a running run

## Then

- start() transitions status to RUNNING and sets started_at timestamp
- complete() transitions status to COMPLETED and sets completed_at timestamp
- cancel() transitions status to CANCELLED and sets completed_at timestamp
- Invalid transitions raise ValueError
