import os
import sys

from openai import OpenAI

from tools import TOOL_SCHEMAS

load_dotenv()

client = OpenAI(
    base_url=os.environ['BASE_URL'],
    api_key=os.environ['OPENROUTER_API_KEY'],
)

def call_llm(messages):
    response = client.chat.completions.create(
        model='deepseek/deepseek-v4.1-flash-1017',
        messages=messages,
        tools=TOOL_SCHEMAS
    )

    output = response.choices[0].message.content

    usage = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
    }

    return output, usage