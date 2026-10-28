---
name: planning
description: Turn an ambiguous or multi-step request into a short, verifiable plan before editing code.
---

# Planning

Use this skill when a request spans multiple files, has unclear requirements, or needs sequencing before implementation.

## Instructions

Inspect the relevant code and configuration before writing the plan. Do not plan around code you have not read.

Restate the goal in one or two sentences so the intended outcome is explicit.

Create a TODO list with `write_todos`. Keep each task small enough to finish and verify independently, and mark exactly one task as in progress.

State assumptions instead of blocking, but ask for clarification when a missing decision would change the design or the files touched.

Note how each task will be verified, such as a command, a test, or an observable behavior.

Update the plan as you learn more. Remove or rewrite tasks that no longer match reality rather than silently doing something else.

Do not edit code while planning unless the plan is already unambiguous and short.
