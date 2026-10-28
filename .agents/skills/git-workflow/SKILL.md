---
name: git-workflow
description: Prepare clean commits, branches, and pull requests that are easy to review.
---

# Git Workflow

Use this skill when committing, branching, resolving conflicts, or preparing a pull request.

## Instructions

Inspect `git status` and `git diff` before staging anything. Understand every change you are about to commit.

Stage only the files that belong to the change. Do not commit unrelated edits, generated files, secrets, or local configuration.

Keep commits logical and self-contained. Write messages that explain why the change is needed, not just what files changed.

Never rewrite history or force-push on shared branches. Do not discard work you did not create; ask before destructive operations.

Resolve conflicts by understanding both sides and preserving the intended behavior, then run the affected tests.

Run the relevant tests before committing or opening a pull request.

In the pull request, describe the problem, the approach, how it was verified, and any risks or follow-up work.
