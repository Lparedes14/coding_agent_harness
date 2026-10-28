---
name: refactoring
description: Restructure existing code without changing observable behavior, verified by tests.
---

# Refactoring

Use this skill when code needs to be reorganized, simplified, or prepared for a larger change without altering behavior.

## Instructions

Establish a baseline before editing: run the relevant tests and note the current behavior.

Keep each step behavior-preserving and small. Typical steps are renaming, extracting a function, moving code, removing duplication, and clarifying control flow.

Do not mix refactoring with functional changes or bug fixes. Complete and verify one kind of change before starting the other.

Preserve public interfaces unless the request includes changing them. When a signature must change, update every caller and report the migration.

Run the tests after each meaningful step. If the area has no tests, characterize the behavior first or add focused tests before restructuring.

Report what changed structurally, confirm that behavior was preserved, and list the commands used to verify it.
