import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOL_SCHEMAS


load_dotenv()

client = OpenAI(
    base_url=os.environ['BASE_URL'],
    api_key=os.environ['OPENROUTER_API_KEY'],
)

SYSTEM_PROMPT = """
You are a coding assistant.
"""

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