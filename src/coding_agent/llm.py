import os

from dotenv import load_dotenv
from openai import OpenAI

from .tools import TOOL_SCHEMAS


load_dotenv()

client = OpenAI(
    base_url=os.environ['BASE_URL'],
    api_key=os.environ['OPENROUTER_API_KEY'],
)

CONVERSATION_COST = 0.0

SYSTEM_PROMPT = ...  # CODE: a system prompt

def call_llm(messages, tools=TOOL_SCHEMAS):
    global CONVERSATION_COST

    request = {
        'model': os.environ['MODEL'],
        'messages': messages,
        'extra_body': {'usage': {'include': True}},
    }

    if tools:
        request['tools'] = tools

    # CODE: send the request to the client
    # CODE: extract the assistant message
    # CODE: extrsct the OpenRouter cost

    if cost is not None:
        CONVERSATION_COST += float(cost)

    usage = {
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'cost': float(cost) if cost is not None else None,
    }

    return message, usage
