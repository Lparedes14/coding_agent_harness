import json
import os

from .llm import call_llm


COMPACT_AT = 30_000

COMPACTION_PROMPT = """
Summarize the coding-agent conversation so work can continue without the
original transcript.

Preserve concrete information, including:

## Goal
What the user ultimately wants.

## Decisions
Important technical and architectural decisions.

## Files Examined
Relevant files and what was learned from them.

## Files Changed
Changes already made and why.

## Commands and Tests
Important command results and test results.

## Current Plan
The current TODO state and progress.

## Failed Approaches
Errors, unsuccessful attempts, and things that should not be repeated.

## Remaining Work
What still needs to happen.

## Next Step
The exact next action the agent should take.

Be concise, but do not omit details needed to continue the task.
""".strip()


def should_compact(usage):
    # TODO(WORKSHOP 2)
    ...

def compact(messages):
    # TODO(WORKSHOP 2)
    ...
