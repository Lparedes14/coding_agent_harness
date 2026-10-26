import json
import os

from . import llm
from .llm import SYSTEM_PROMPT, call_llm
from .tools import MARKS, TODOS, TOOL_SCHEMAS, TOOLS


MAX_STEPS = 50


HELP = """
Commands:
  /help      Show available commands
  /new       Start a new conversation
  /todos     Show the current plan
  /model     Show the current model
  /quit      Exit
""".strip()


def run_agent(messages, show=True, on_event=None):
    total_usage = {
        'prompt_tokens': 0,
        'completion_tokens': 0,
    }

    for _ in range(MAX_STEPS):
        # CODE: call the LLM

        # CODE: record and display response

        # CODE: stop if there are no tool calls

        # CODE: execute every requested tool

        # CODE: append matching tool results

        ...

    return '', total_usage

def main():
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
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
                {'role': 'system', 'content': SYSTEM_PROMPT},
            ]
            TODOS.clear()
            llm.CONVERSATION_COST = 0.0
            print("Started a new conversation.")
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
            starting_cost = llm.CONVERSATION_COST
            _, usage = run_agent(messages)
            turn_cost = llm.CONVERSATION_COST - starting_cost

            print(
                "Tokens: "
                f"{usage['prompt_tokens']:,} prompt + "
                f"{usage['completion_tokens']:,} completion"
            )
            print(
                f"Cost: ${turn_cost:.6f} this turn · "
                f"${llm.CONVERSATION_COST:.6f} conversation"
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
