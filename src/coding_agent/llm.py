import os

from dotenv import load_dotenv
from openai import OpenAI

from .tools import TOOL_SCHEMAS


load_dotenv()

client = OpenAI(
    base_url=os.environ['BASE_URL'],
    api_key=os.environ['OPENROUTER_API_KEY'],
)

SYSTEM_PROMPT = """
You are a coding agent working in the current directory.

Use the available tools to inspect the project before making changes. Keep
working until the user's request is complete.

For multi-step tasks, use write_todos and keep the plan updated. If an
available skill matches the task, read it before acting. Use task for focused,
read-only codebase exploration.

Prefer small, targeted edits. After changing code, run the relevant tests or
checks. Never claim a check passed unless you ran it.

In the final response, briefly explain what changed, what you tested, and
anything that remains unresolved.
""".strip()

def call_llm(messages, tools=TOOL_SCHEMAS):
    request = {
        'model': os.environ['MODEL'],
        'messages': messages,
    }

    if tools:
        request['tools'] = tools

    response = client.chat.completions.create(**request)

    message = response.choices[0].message

    usage = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
    }

    return message, usage
