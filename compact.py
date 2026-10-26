import json
import os

from llm import call_llm

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
    return usage.get('prompt_tokens', 0) >= COMPACT_AT

def compact(messages):
    if not messages:
        return messages

    transcript = json.dumps(
        messages,
        ensure_ascii=False,
        indent=2,
    )

    summary_message, _ = call_llm([
        {'role': 'system', 'content': COMPACTION_PROMPT},
        {'role': 'user', 'content': transcript},
    ])

    return [
        {'role': 'user', 'content': 'The earlier conversation was compacted into the following working context. Use it as context and continue from the recorded state.\n\n' + summary_message.content}
    ]