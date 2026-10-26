import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path.cwd() / '.env')

client = None

SYSTEM_PROMPT = """
You are a coding agent working in the current project.

Inspect relevant files before changing them. Use tools to continue working
until the user's request is actually complete.

For multi-step work, use write_todos and keep exactly one item in progress
while unfinished work remains.
Use read_skill when an available skill matches the task. Use task for focused,
read-only codebase exploration that would otherwise fill the main conversation
with search results.

Prefer targeted edits over rewriting entire existing files. After making
changes, run the most relevant available checks. Never claim a test or command
passed unless you actually ran it.

Keep explanations concise and clearly report what changed, what was verified,
and anything that remains unresolved.
""".strip()


def call_llm(messages, tools=None):
    global client

    required = ('BASE_URL', 'OPENROUTER_API_KEY', 'MODEL')
    missing = [name for name in required if not os.environ.get(name)]

    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in the values."
        )

    if client is None:
        client = OpenAI(
            base_url=os.environ['BASE_URL'],
            api_key=os.environ['OPENROUTER_API_KEY'],
        )

    request = {
        'model': os.environ['MODEL'],
        'messages': messages,
    }

    if tools is not None:
        request['tools'] = tools

    response = client.chat.completions.create(**request)

    message = response.choices[0].message

    response_usage = response.usage
    usage = {
        'prompt_tokens': response_usage.prompt_tokens if response_usage else 0,
        'completion_tokens': (
            response_usage.completion_tokens if response_usage else 0
        ),
    }

    return message, usage
