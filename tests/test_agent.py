import json
from types import SimpleNamespace

import pytest

from coding_agent import agent, compact, llm, skills, subagent


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []

    def model_dump(self, exclude_none=True):
        message = {'role': 'assistant'}

        if self.content is not None:
            message['content'] = self.content

        if self.tool_calls:
            message['tool_calls'] = [
                {
                    'id': call.id,
                    'type': 'function',
                    'function': {
                        'name': call.function.name,
                        'arguments': call.function.arguments,
                    },
                }
                for call in self.tool_calls
            ]

        return message


def make_tool_call(name, arguments, call_id='call-1'):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments),
        ),
    )


def test_llm_requires_configuration(monkeypatch):
    for name in ('BASE_URL', 'OPENROUTER_API_KEY', 'MODEL'):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setattr(llm, 'client', None)

    with pytest.raises(RuntimeError, match='Missing environment variables'):
        llm.call_llm([{'role': 'user', 'content': 'hello'}])


def test_llm_can_make_a_tool_free_request_without_usage(monkeypatch):
    for name, value in {
        'BASE_URL': 'https://example.invalid/v1',
        'OPENROUTER_API_KEY': 'test-key',
        'MODEL': 'test-model',
    }.items():
        monkeypatch.setenv(name, value)

    response = SimpleNamespace(
        choices=[SimpleNamespace(message=FakeMessage('summary'))],
        usage=None,
    )
    create = lambda **kwargs: response
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create),
        ),
    )
    monkeypatch.setattr(llm, 'client', fake_client)

    message, usage = llm.call_llm(
        [{'role': 'user', 'content': 'hello'}],
        tools=None,
    )

    assert message.content == 'summary'
    assert usage == {'prompt_tokens': 0, 'completion_tokens': 0}


def test_agent_runs_tool_and_continues(monkeypatch, tmp_path):
    path = tmp_path / 'example.txt'
    path.write_text('hello')
    call = make_tool_call('read_file', {'file_path': str(path)})
    responses = iter([
        (
            FakeMessage(tool_calls=[call]),
            {'prompt_tokens': 10, 'completion_tokens': 1},
        ),
        (
            FakeMessage('finished'),
            {'prompt_tokens': 20, 'completion_tokens': 2},
        ),
    ])
    monkeypatch.setattr(agent, 'call_llm', lambda *args, **kwargs: next(responses))
    messages = [
        {'role': 'system', 'content': 'system'},
        {'role': 'user', 'content': 'read it'},
    ]

    content, usage = agent.run_agent(messages, show=False)

    tool_result = next(message for message in messages if message['role'] == 'tool')
    assert tool_result['tool_call_id'] == 'call-1'
    assert tool_result['content'] == 'hello'
    assert content == 'finished'
    assert usage == {'prompt_tokens': 30, 'completion_tokens': 3}


def test_agent_turns_bad_arguments_into_a_tool_result(monkeypatch):
    bad_call = SimpleNamespace(
        id='bad-call',
        function=SimpleNamespace(
            name='read_file',
            arguments='{not-json',
        ),
    )
    responses = iter([
        (
            FakeMessage(tool_calls=[bad_call]),
            {'prompt_tokens': 1, 'completion_tokens': 1},
        ),
        (
            FakeMessage('recovered'),
            {'prompt_tokens': 2, 'completion_tokens': 1},
        ),
    ])
    monkeypatch.setattr(agent, 'call_llm', lambda *args, **kwargs: next(responses))
    messages = [
        {'role': 'system', 'content': 'system'},
        {'role': 'user', 'content': 'continue'},
    ]

    content, _ = agent.run_agent(messages, show=False)

    tool_result = next(message for message in messages if message['role'] == 'tool')
    assert tool_result['content'].startswith('Error: JSONDecodeError')
    assert content == 'recovered'


def test_compaction_replaces_history_and_restores_system_prompt(monkeypatch):
    monkeypatch.setattr(
        agent,
        'compact',
        lambda messages: [{'role': 'user', 'content': 'summary'}],
    )
    messages = [
        {'role': 'system', 'content': 'old system'},
        {'role': 'user', 'content': 'old conversation'},
    ]

    assert agent.compact_history(messages) is True
    assert messages[0]['role'] == 'system'
    assert 'Available skills:' in messages[0]['content']
    assert messages[1] == {'role': 'user', 'content': 'summary'}


def test_compactor_disables_tools(monkeypatch):
    calls = []

    def fake_call(messages, tools='not-set'):
        calls.append(tools)
        return FakeMessage('summary'), {
            'prompt_tokens': 1,
            'completion_tokens': 1,
        }

    monkeypatch.setattr(compact, 'call_llm', fake_call)

    result = compact.compact([{'role': 'user', 'content': 'history'}])

    assert calls == [None]
    assert 'summary' in result[0]['content']


def test_skills_are_discovered_and_advertised(monkeypatch, tmp_path):
    skill = tmp_path / 'review' / 'SKILL.md'
    skill.parent.mkdir()
    skill.write_text('# Review\nInspect the change.')
    monkeypatch.setattr(skills, 'SKILLS_DIR', tmp_path)

    assert skills.list_skills() == ['review']
    assert skills.read_skill('review').startswith('# Review')
    assert 'Available skills: review' in agent.build_system_prompt()


def test_subagent_has_fresh_context_and_restricted_tools(monkeypatch):
    captured = []

    def fake_call(messages, tools=None):
        captured.append(([message.copy() for message in messages], tools))
        return FakeMessage('report'), {
            'prompt_tokens': 1,
            'completion_tokens': 1,
        }

    monkeypatch.setattr(subagent, 'call_llm', fake_call)

    assert subagent.task('Inspect the parser') == 'report'
    assert len(captured[0][0]) == 2
    assert captured[0][0][1] == {
        'role': 'user',
        'content': 'Inspect the parser',
    }
    assert set(subagent.SUBAGENT_TOOLS) == {'bash', 'read_file'}
    assert all(
        schema['function']['name'] in {'bash', 'read_file'}
        for schema in captured[0][1]
    )


def test_cli_can_exit_without_calling_the_model(monkeypatch, capsys):
    monkeypatch.setattr('builtins.input', lambda prompt='': '/quit')

    agent.main()

    output = capsys.readouterr().out
    assert 'Coding agent ready.' in output
    assert 'Exiting' in output
