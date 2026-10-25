import json

from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS


try:
    # Conversation loop (continue until Ctrl+C)
    while True:
        user_input = input("Enter your prompt> ")

        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_input}
        ]

        # Agent loop (runs until current request is finished)
        while True:
            message, usage = call_llm(messages)
            messages.append(message.model_dump(exclude_none=True))

            if message.content:
                print("\nAgent: ", message.content, "\n")

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = TOOLS[tool_call.function.name](**args)

                print("Tool: ", tool_call.function.name, args)
                print(result, "\n")

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call.id,
                    'content': result,
                })

            print(usage)

except KeyboardInterrupt:
    print("\nExiting")