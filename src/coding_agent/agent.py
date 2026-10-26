import json
import os

from compact import compact, should_compact
from llm import SYSTEM_PROMPT, call_llm
from skills import READ_SKILL_SCHEMA, list_skills, read_skill
from subagent import TASK_SCHEMA, task
from tools import MARKS, TODOS
from tools import TOOL_SCHEMAS as BASE_TOOL_SCHEMAS
from tools import TOOLS as BASE_TOOLS


MAX_STEPS = 50
MAX_TOOL_OUTPUT = 30_000
MAX_DISPLAY_LINES = 12

AGENT_TOOLS = {
    **BASE_TOOLS,
    'read_skill': read_skill,
    'task': task,
}

AGENT_TOOL_SCHEMAS = [
    *BASE_TOOL_SCHEMAS,
    READ_SKILL_SCHEMA,
    TASK_SCHEMA,
]

HELP = """
Commands:
  /help      Show available commands
  /new       Start a new conversation
  /compact   Compact the conversation now
  /todos     Show the current plan
  /skills    Show available skills
  /model     Show the current model
  /quit      Exit
""".strip()


def build_system_prompt():
    skills = ', '.join(list_skills()) or 'none'

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Available skills: {skills}. "
        "When a skill matches the task, call read_skill before acting."
    )


def compact_history(messages):
    if len(messages) <= 1:
        return False

    compacted = compact(messages[1:])

    messages[:] = [
        {'role': 'system', 'content': build_system_prompt()},
        *compacted,
    ]

    return True


def run_agent(messages, show=True):
    total_usage = {
        'prompt_tokens': 0,
        'completion_tokens': 0,
    }

    last_content = ''

    for _ in range(MAX_STEPS):
        message, usage = call_llm(
            messages,
            tools=AGENT_TOOL_SCHEMAS,
        )

        total_usage['prompt_tokens'] += usage.get('prompt_tokens', 0) or 0
        total_usage['completion_tokens'] += (
            usage.get('completion_tokens', 0) or 0
        )

        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            last_content = message.content

            if show:
                print(f"\nAgent:\n{message.content}\n")

        done = not message.tool_calls

        for tool_call in message.tool_calls or []:
            name = tool_call.function.name
            raw_args = tool_call.function.arguments or '{}'

            if show:
                preview = ' '.join(raw_args.split())
                if len(preview) > 500:
                    preview = preview[:500] + '...'

                print(f"Tool: {name} {preview}")

            try:
                args = json.loads(raw_args)

                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be a JSON object")

                tool = AGENT_TOOLS.get(name)

                if tool is None:
                    raise ValueError(f"Unknown tool `{name}`")

                result = tool(**args)

                if not isinstance(result, str):
                    result = json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str,
                    )

            except Exception as error:
                result = f"Error: {type(error).__name__}: {error}"

            if len(result) > MAX_TOOL_OUTPUT:
                keep = MAX_TOOL_OUTPUT // 2
                removed = len(result) - MAX_TOOL_OUTPUT

                result = (
                    f"{result[:keep]}\n"
                    f"... [{removed} characters truncated] ...\n"
                    f"{result[-keep:]}"
                )

            if show:
                lines = result.splitlines() or ['(no output)']
                displayed = lines[:MAX_DISPLAY_LINES]
                hidden = len(lines) - len(displayed)

                print('\n'.join(displayed))

                if hidden:
                    print(f"... {hidden} more lines")

                print()

            messages.append({
                'role': 'tool',
                'tool_call_id': tool_call.id,
                'content': result,
            })

        # Compact only after all tool calls have matching tool results.
        if should_compact(usage):
            try:
                compact_history(messages)

                if show:
                    print("[Conversation compacted]\n")

            except Exception as error:
                if show:
                    print(
                        f"[Compaction skipped: "
                        f"{type(error).__name__}: {error}]\n"
                    )

        if done:
            return last_content, total_usage

    if show:
        print(f"Agent stopped after {MAX_STEPS} steps.")

    return last_content, total_usage


def main():
    messages = [
        {'role': 'system', 'content': build_system_prompt()},
    ]

    print("Coding agent ready.")
    print(f"Model: {os.environ.get('MODEL', 'not configured')}")
    print(f"Working directory: {os.getcwd()}")
    print("Type /help for commands.")

    while True:
        try:
            user_input = input("\nYou> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        command = user_input.lower()

        if command in {'/quit', '/exit'}:
            break

        if command == '/help':
            print(HELP)
            continue

        if command == '/new':
            messages[:] = [
                {'role': 'system', 'content': build_system_prompt()},
            ]
            TODOS.clear()
            print("Started a new conversation.")
            continue

        if command == '/compact':
            try:
                if compact_history(messages):
                    print("Conversation compacted.")
                else:
                    print("There is nothing to compact yet.")
            except Exception as error:
                print(
                    f"Compaction failed: "
                    f"{type(error).__name__}: {error}"
                )

            continue

        if command == '/todos':
            if not TODOS:
                print("No todos.")
            else:
                for todo in TODOS:
                    status = todo.get('status', 'pending')

                    if status == 'in_progress':
                        text = (
                            todo.get('activeForm')
                            or todo.get('content', '')
                        )
                    else:
                        text = todo.get('content', '')

                    print(f"{MARKS.get(status, '[?]')} {text}")

            continue

        if command == '/skills':
            skills = list_skills()

            if skills:
                print('\n'.join(f"- {skill}" for skill in skills))
            else:
                print("No skills found.")

            continue

        if command == '/model':
            print(os.environ.get('MODEL', 'MODEL is not configured'))
            continue

        if command.startswith('/'):
            print(f"Unknown command: {user_input}")
            continue

        messages.append({
            'role': 'user',
            'content': user_input,
        })

        try:
            _, usage = run_agent(messages)

            print(
                "Tokens: "
                f"{usage['prompt_tokens']:,} prompt + "
                f"{usage['completion_tokens']:,} completion"
            )

        except KeyboardInterrupt:
            print("\nStopped.")
            break

        except Exception as error:
            print(
                f"\nAgent error: "
                f"{type(error).__name__}: {error}"
            )

    print("\nExiting")


if __name__ == '__main__':
    main()