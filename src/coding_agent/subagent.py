import json
import os

from .llm import call_llm
from .tools import TOOL_SCHEMAS, TOOLS


MAX_STEPS = 12
MAX_TOOL_OUTPUT = 20_000

SUBAGENT_PROMPT = f"""
You are a focused codebase exploration subagent.

You were given one self-contained question by a lead coding agent. You cannot
see the lead agent's conversation. Only your final response will be returned
to it.

You are working in:
{os.getcwd()}

Use the available tools to investigate what is actually true.

Rules:
- Read and report. Do not edit files or intentionally change the project.
- Search only inside the current project.
- Prefer rg and targeted file reads over broad searches.
- Include relevant file paths and concrete findings.
- Stop once you can answer the question.
- Keep the final report concise.
- Do not try to create another subagent.
""".strip()

SUBAGENT_TOOLS = {
    name: TOOLS[name]
    for name in ('bash', 'read_file')
}

SUBAGENT_TOOL_SCHEMAS = [
    schema
    for schema in TOOL_SCHEMAS
    if schema['function']['name'] in SUBAGENT_TOOLS
]


def task(description: str) -> str:
    messages = [
        {'role': 'system', 'content': SUBAGENT_PROMPT},
        {'role': 'user', 'content': description},
    ]

    last_content = ''

    for _ in range(MAX_STEPS):
        message, _ = call_llm(
            messages,
            tools=SUBAGENT_TOOL_SCHEMAS,
        )

        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            last_content = message.content

        if not message.tool_calls:
            return (
                last_content
                or "The subagent returned no findings."
            )

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            raw_args = tool_call.function.arguments or '{}'

            try:
                args = json.loads(raw_args)

                if not isinstance(args, dict):
                    raise ValueError(
                        "Tool arguments must be a JSON object"
                    )

                tool = SUBAGENT_TOOLS.get(name)

                if tool is None:
                    raise ValueError(
                        f"Tool `{name}` is not available"
                    )

                result = tool(**args)

                if not isinstance(result, str):
                    result = json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str,
                    )

            except Exception as error:
                result = (
                    f"Error: {type(error).__name__}: {error}"
                )

            if len(result) > MAX_TOOL_OUTPUT:
                keep = MAX_TOOL_OUTPUT // 2
                removed = len(result) - MAX_TOOL_OUTPUT

                result = (
                    f"{result[:keep]}\n"
                    f"... [{removed} characters truncated] ...\n"
                    f"{result[-keep:]}"
                )

            messages.append({
                'role': 'tool',
                'tool_call_id': tool_call.id,
                'content': result,
            })

    messages.append({
        'role': 'user',
        'content': (
            "You have reached the exploration limit. "
            "Return your best findings now without using more tools."
        ),
    })

    message, _ = call_llm(messages, tools=None)

    return (
        message.content
        or last_content
        or "The subagent reached its limit without a result."
    )


TASK_SCHEMA = {
    'type': 'function',
    'function': {
        'name': 'task',
        'description': (
            "Delegate a focused, read-only codebase investigation to a "
            "fresh subagent with its own context. It cannot see the current "
            "conversation, so provide a complete standalone description."
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'description': {
                    'type': 'string',
                    'description': (
                        "The complete question, where to investigate, "
                        "and what the returned report should contain"
                    ),
                },
            },
            'required': ['description'],
        },
    },
}
