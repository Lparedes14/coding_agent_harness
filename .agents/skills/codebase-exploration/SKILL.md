---
name: codebase-exploration
description: Map an unfamiliar codebase and report its structure, entry points, and conventions without changing files.
---

# Codebase Exploration

Use this skill when starting work in an unfamiliar repository or when you need to find where existing behavior lives.

## Instructions

Explore only; do not edit files.

Start with the README, dependency manifest, and configuration files to learn how the project is built and run.

Identify the entry points, the main modules, and how data or requests flow between them. Trace one representative feature end to end.

Record the conventions that new code must follow: naming, error handling, logging, testing, formatting, and directory layout.

Search for symbols and strings instead of reading every file. Prefer targeted searches over broad file dumps.

For a wide, read-only investigation, consider delegating to the `task` subagent and then verifying its key claims yourself.

Report the project's purpose, layout, entry points, key modules, conventions, and any gaps or risks. Cite file paths, and say explicitly what you did not inspect.
