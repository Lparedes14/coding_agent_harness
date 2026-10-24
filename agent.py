import json

from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS

user_input = input("Enter your prompt> ")

messages = [
    {'role': 'system', 'content': SYSTEM_PROMPT},
    {'role': 'user', 'content': user_input}
]

while True:
    message, usage = call_llm(messages)
    messages.append(message.model_dump(exclude_none=True))