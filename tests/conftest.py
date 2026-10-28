import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

# Keep tests independent of a developer's .env and run them from the
# repository root, where the agent expects .agents/skills to live.
# Set the environment before importing coding_agent.llm, which builds its
# OpenAI client at import time.
os.chdir(ROOT)
os.environ.setdefault('BASE_URL', 'https://openrouter.ai/api/v1')
os.environ.setdefault('OPENROUTER_API_KEY', 'test-key')
os.environ.setdefault('MODEL', 'test/model')

from coding_agent import llm  # noqa: E402
from coding_agent.tools import TODOS  # noqa: E402


@pytest.fixture(autouse=True)
def clean_agent_state():
    llm.CONVERSATION_COST = 0.0
    TODOS.clear()

    yield

    llm.CONVERSATION_COST = 0.0
    TODOS.clear()
