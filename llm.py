import os
import sys

from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ['BASE_URL'],
    api_key=os.environ['OPENROUTER_API_KEY'],
)

user_input = input("Enter your prompt> ")

SYSTEM_PROMPT = """
You are a coding agent. Your job is to code.
"""

response = client.chat.completions.create(
    model='deepseek/deepseek-v4.1-flash-1017',
    messages=[
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_input}
    ]
)

output = response.choices[0].message.content

usage = {
    'prompt_tokens': response.usage.prompt_tokens,
    'completion_tokens': response.usage.completion_tokens,
}

print(f"\nAgent: {output} \n")
print(usage)