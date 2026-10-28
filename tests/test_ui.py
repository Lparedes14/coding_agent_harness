import asyncio
import time

import pytest
from textual.widgets import Input, RichLog

import coding_agent.ui as ui
from coding_agent import llm


class RecordingApp(ui.GuildAgentApp):
    def __init__(self):
        super().__init__()
        self.tool_events = []
        self.todo_renders = []

    def _write_tool(self, data):
        self.tool_events.append(data['name'])
        super()._write_tool(data)

    def _write_todos(self, todos):
        self.todo_renders.append(todos)
        super()._write_todos(todos)


async def wait_until(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout

    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError('Timed out waiting for the UI to settle.')
        await asyncio.sleep(0.01)


async def submit(app, pilot, text):
    prompt = app.query_one('#prompt', Input)
    prompt.value = text
    await pilot.press('enter')
    await pilot.pause()


@pytest.mark.asyncio
async def test_app_mounts_with_expected_widgets():
    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        prompt = app.query_one('#prompt', Input)

        assert app.focused is prompt
        assert prompt.placeholder
        assert str(app.query_one('#status').content) == 'Ready'
        assert app.query_one('#usage').content == ''
        assert isinstance(app.query_one('#transcript'), RichLog)
        assert len(app.messages) == 1
        assert app.messages[0]['role'] == 'system'

        context = str(app.query_one('#context').content)
        assert 'MODEL' in context
        assert 'CWD' in context
        assert 'SKILLS' in context


@pytest.mark.asyncio
@pytest.mark.parametrize('size', [(80, 24), (60, 20)])
async def test_app_mounts_in_small_terminals(size):
    app = ui.GuildAgentApp()

    async with app.run_test(size=size) as pilot:
        await pilot.pause()

        assert app.focused is app.query_one('#prompt', Input)
        assert app.query_one('#context').content
        assert str(app.query_one('#status').content) == 'Ready'


@pytest.mark.asyncio
async def test_commands_do_not_invoke_the_agent(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError('The agent should not run for a command.')

    monkeypatch.setattr(ui, 'run_agent', fail)

    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        for command in ['/help', '/skills', '/model', '/todos', '/nope']:
            await submit(app, pilot, command)

            assert app.running is False
            assert app.query_one('#prompt', Input).disabled is False
            assert str(app.query_one('#status').content) == 'Ready'

        assert len(app.messages) == 1


@pytest.mark.asyncio
async def test_turn_renders_events_and_usage(monkeypatch):
    def fake_run_agent(messages, show=True, on_event=None):
        llm.CONVERSATION_COST += 0.00042

        on_event('assistant', {'content': 'Checking the project.'})
        on_event('tool', {
            'name': 'bash',
            'args': {'command': 'python -m pytest -q'},
            'result': '1 failed, 7 passed in 0.19s',
        })
        on_event('tool', {
            'name': 'write_todos',
            'args': {'todos': [
                {
                    'content': 'Inspect the project',
                    'activeForm': 'Inspecting the project',
                    'status': 'done',
                },
                {
                    'content': 'Fix the bug',
                    'activeForm': 'Fixing the bug',
                    'status': 'in_progress',
                },
            ]},
            'result': 'Todo list updated',
        })
        on_event('assistant', {'content': 'Fixed the calculation bug.'})

        return 'Fixed the calculation bug.', {
            'prompt_tokens': 1_234,
            'completion_tokens': 56,
        }

    monkeypatch.setattr(ui, 'run_agent', fake_run_agent)

    app = RecordingApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await submit(app, pilot, 'Fix the failing test')
        await wait_until(lambda: not app.running)

        assert app.messages[-1] == {
            'role': 'user',
            'content': 'Fix the failing test',
        }
        assert app.tool_events == ['bash', 'write_todos']
        assert len(app.todo_renders) == 1
        assert len(app.todo_renders[0]) == 2

        status = str(app.query_one('#status').content)
        usage = str(app.query_one('#usage').content)

        assert status == 'Ready'
        assert '1,234 in / 56 out' in usage
        assert '$0.000420 turn' in usage
        assert '$0.000420 total' in usage
        assert app.query_one('#prompt', Input).disabled is False


@pytest.mark.asyncio
async def test_agent_failure_is_shown_and_prompt_recovers(monkeypatch):
    def explode(messages, show=True, on_event=None):
        raise RuntimeError('network unavailable')

    monkeypatch.setattr(ui, 'run_agent', explode)

    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await submit(app, pilot, 'Do some work')
        await wait_until(lambda: not app.running)

        prompt = app.query_one('#prompt', Input)

        assert str(app.query_one('#status').content) == 'Ready after error'
        assert prompt.disabled is False
        assert app.focused is prompt
        assert app.messages[-1]['role'] == 'user'


@pytest.mark.asyncio
async def test_new_chat_shortcut_resets_state():
    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        llm.CONVERSATION_COST = 1.25
        ui.TODOS.extend([
            {
                'content': 'Old task',
                'activeForm': 'Doing old task',
                'status': 'pending',
            },
        ])
        app.messages.append({'role': 'user', 'content': 'Old message'})

        await pilot.press('ctrl+n')
        await pilot.pause()

        assert llm.CONVERSATION_COST == 0.0
        assert ui.TODOS == []
        assert len(app.messages) == 1
        assert app.messages[0]['role'] == 'system'
        assert app.query_one('#prompt', Input).value == ''
        assert str(app.query_one('#status').content) == 'Ready'


@pytest.mark.asyncio
async def test_busy_app_ignores_new_prompts():
    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        app.running = True
        await submit(app, pilot, 'Second request')

        assert len(app.messages) == 1


@pytest.mark.asyncio
async def test_compact_without_history_is_a_noop():
    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await submit(app, pilot, '/compact')

        assert app.running is False
        assert str(app.query_one('#status').content) == 'Ready'
        assert app.query_one('#prompt', Input).disabled is False


@pytest.mark.asyncio
async def test_compact_command_reports_success(monkeypatch):
    def fake_compact(messages):
        messages[:] = [
            messages[0],
            {'role': 'assistant', 'content': 'Summary of the work so far.'},
        ]
        return True

    monkeypatch.setattr(ui, 'compact_history', fake_compact)

    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        app.messages.extend([
            {'role': 'user', 'content': 'Long request'},
            {'role': 'assistant', 'content': 'Long response'},
        ])

        await submit(app, pilot, '/compact')
        await wait_until(lambda: not app.running)

        assert len(app.messages) == 2
        assert app.messages[-1]['content'].startswith('Summary')
        assert str(app.query_one('#status').content) == 'Ready'
        assert 'compact' in str(app.query_one('#usage').content).lower()


@pytest.mark.asyncio
async def test_compact_failure_keeps_conversation(monkeypatch):
    def explode(messages):
        raise RuntimeError('compaction unavailable')

    monkeypatch.setattr(ui, 'compact_history', explode)

    app = ui.GuildAgentApp()

    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        app.messages.extend([
            {'role': 'user', 'content': 'Long request'},
            {'role': 'assistant', 'content': 'Long response'},
        ])
        before = [dict(message) for message in app.messages]

        await submit(app, pilot, '/compact')
        await wait_until(lambda: not app.running)

        assert app.messages == before
        assert str(app.query_one('#status').content) == 'Ready after error'
        assert app.query_one('#prompt', Input).disabled is False


def test_shorten_path_keeps_tail():
    rendered = ui._shorten_path('C:/one/two/three/four/five', limit=20)

    assert rendered.startswith('...')
    assert rendered.endswith('five')
    assert len(rendered) <= 20


def test_format_args_is_readable():
    command = ui._format_args({'command': 'echo hello'})
    assert str(command) == '$ echo hello'

    generic = ui._format_args({'file_path': 'README.md', 'n': 2})
    assert str(generic) == 'file_path: README.md\nn: 2'

    empty = ui._format_args({})
    assert str(empty) == '(no arguments)'


def test_long_argument_is_truncated():
    rendered = str(ui._format_args({'content': 'x' * 2_000}))
    assert rendered.endswith('...')
    assert len(rendered) <= ui.MAX_ARG_CHARS + len('content: ') + 3


def test_error_detection():
    assert ui._looks_like_error('Error: permission denied')
    assert ui._looks_like_error('Exit code 1\nfailed')
    assert not ui._looks_like_error('7 passed')
