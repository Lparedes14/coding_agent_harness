"""Textual terminal frontend for the guild coding agent.

The UI is intentionally a thin presentation layer over ``agent.run_agent``.
It owns no agent loop of its own: the same messages, tools, skills, TODOs,
and cost counters used by the plain CLI drive this interface.
"""

import json
import os
from pathlib import Path

from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Input, RichLog, Static

from . import llm
from .agent import build_system_prompt, compact_history, run_agent
from .skills import list_skills
from .tools import MARKS, TODOS


YELLOW = '#ffd21c'
ORANGE = '#ffb000'
BLACK = '#080808'
SURFACE = '#151515'
MUTED = '#8b8b8b'
TEXT = '#f5f5f5'
ERROR = '#ff6b6b'

MAX_TOOL_LINES = 12
MAX_ARG_CHARS = 500


COMMAND_ROWS = [
    ('/help', 'Show available commands'),
    ('/new', 'Clear the conversation, TODOs, and cost total'),
    ('/compact', 'Summarize the conversation into a smaller context'),
    ('/todos', 'Show the current plan'),
    ('/skills', 'List the discoverable skills'),
    ('/model', 'Show the configured model'),
    ('/quit', 'Exit the agent'),
    ('Ctrl+N', 'Start a new conversation'),
    ('Ctrl+Q', 'Quit'),
    ('Esc', 'Focus the prompt'),
]


class GuildAgentApp(App):
    """Terminal interface for the coding harness."""

    TITLE = 'INIT AI Guild Coding Agent'
    SUB_TITLE = os.environ.get('MODEL', 'model not configured')

    CSS = f"""
    Screen {{
        background: {BLACK};
        color: {TEXT};
    }}

    Header {{
        background: {YELLOW};
        color: {BLACK};
        text-style: bold;
    }}

    #context {{
        height: 4;
        padding: 0 2;
        background: {SURFACE};
        color: {MUTED};
        border-bottom: solid {ORANGE};
    }}

    #transcript {{
        height: 1fr;
        padding: 1 2;
        background: {BLACK};
        scrollbar-color: {YELLOW};
        scrollbar-color-hover: {ORANGE};
        scrollbar-color-active: {ORANGE};
    }}

    #statusbar {{
        height: 1;
        background: {SURFACE};
        layout: horizontal;
    }}

    #status {{
        width: auto;
        height: 1;
        padding: 0 2;
        color: {YELLOW};
        content-align: left middle;
    }}

    #usage {{
        width: 1fr;
        height: 1;
        padding: 0 2;
        color: {MUTED};
        content-align: right middle;
    }}

    #prompt {{
        height: 3;
        margin: 0 1;
        border: tall {MUTED};
        background: {SURFACE};
        color: #ffffff;
    }}

    #prompt:focus {{
        border: tall {YELLOW};
    }}

    #prompt:disabled {{
        border: tall {MUTED};
        color: {MUTED};
    }}

    Footer {{
        background: {BLACK};
        color: {MUTED};
    }}

    Footer > .footer--highlight {{
        background: {YELLOW};
        color: {BLACK};
    }}
    """

    BINDINGS = [
        ('ctrl+q', 'quit', 'Quit'),
        ('ctrl+n', 'new_chat', 'New chat'),
        ('escape', 'focus_prompt', 'Focus input'),
    ]

    def __init__(self):
        super().__init__()
        self.messages = [
            {'role': 'system', 'content': build_system_prompt()},
        ]
        self.running = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(self._context_text(), id='context')
        yield RichLog(
            id='transcript',
            max_lines=5_000,
            min_width=0,
            wrap=True,
            highlight=False,
            markup=False,
        )
        with Horizontal(id='statusbar'):
            yield Static('Ready', id='status')
            yield Static('', id='usage')
        yield Input(
            placeholder=(
                'Ask the agent to inspect, build, or fix something. '
                '(/help for commands)'
            ),
            id='prompt',
        )
        yield Footer()

    def on_mount(self):
        self._welcome()
        self.query_one('#prompt', Input).focus()

    # ------------------------------------------------------------------
    # Input and commands
    # ------------------------------------------------------------------

    @on(Input.Submitted)
    def submit(self, event: Input.Submitted):
        text = event.value.strip()

        if not text or self.running:
            return

        event.input.value = ''

        if text.startswith('/'):
            self._command(text)
            return

        self._write_user(text)
        self.messages.append({'role': 'user', 'content': text})
        self._busy('Thinking')
        self.run_turn()

    def _command(self, text):
        command = text.split(maxsplit=1)[0].lower()

        if command in {'/quit', '/exit'}:
            self.exit()
        elif command == '/help':
            self._write_help()
        elif command == '/new':
            self.action_new_chat()
        elif command == '/compact':
            self._start_compaction()
        elif command == '/todos':
            self._write_todos(TODOS)
        elif command == '/skills':
            self._write_skills()
        elif command == '/model':
            self._write_model()
        else:
            self._write_note(f'Unknown command: {command}')
            self._write_note('Type /help to see the available commands.')

    # ------------------------------------------------------------------
    # Agent worker
    # ------------------------------------------------------------------

    @work(thread=True, exclusive=True, exit_on_error=False)
    def run_turn(self):
        starting_cost = llm.CONVERSATION_COST

        try:
            _, usage = run_agent(
                self.messages,
                show=False,
                on_event=self._agent_event,
            )
        except Exception as error:
            self.call_from_thread(self._turn_failed, error)
            return

        turn_cost = llm.CONVERSATION_COST - starting_cost
        self.call_from_thread(self._turn_finished, usage, turn_cost)

    @work(thread=True, exclusive=True, exit_on_error=False)
    def compact_conversation(self):
        starting_cost = llm.CONVERSATION_COST
        before = len(self.messages)

        try:
            changed = compact_history(self.messages)
        except Exception as error:
            self.call_from_thread(self._compaction_failed, error)
            return

        cost = llm.CONVERSATION_COST - starting_cost
        self.call_from_thread(
            self._compaction_finished,
            changed,
            before,
            cost,
        )

    def _agent_event(self, kind, data):
        self.call_from_thread(self._display_event, kind, data)

    def _display_event(self, kind, data):
        if kind == 'assistant':
            self._write_agent(data['content'])
            self._set_status('Thinking', '')
        elif kind == 'tool':
            self._write_tool(data)
            self._set_status(f"Ran {data.get('name', 'tool')}", '')
        elif kind == 'compacted':
            self._write_note(
                f"Conversation compacted: "
                f"{data['before']} -> {data['after']} messages"
            )
        elif kind == 'note':
            self._write_note(data['content'])

    def _turn_finished(self, usage, turn_cost):
        self._mark_ready()

        prompt_tokens = usage.get('prompt_tokens', 0) or 0
        completion_tokens = usage.get('completion_tokens', 0) or 0
        usage_text = (
            f'{prompt_tokens:,} in / {completion_tokens:,} out'
            f'  |  ${turn_cost:.6f} turn'
            f'  |  ${llm.CONVERSATION_COST:.6f} total'
        )
        self._set_status('Ready', usage_text)

    def _turn_failed(self, error):
        self._mark_ready()
        self._set_status(
            'Ready after error',
            f'${llm.CONVERSATION_COST:.6f} conversation',
        )
        self._write_panel(
            'error',
            Group(
                Text(
                    f'{type(error).__name__}: {error}',
                    style=f'bold {ERROR}',
                ),
                Text(''),
                Text(
                    'Check .env, network access, and that the configured '
                    'model supports tool calling.',
                    style=MUTED,
                ),
            ),
            border=ERROR,
        )

    def _start_compaction(self):
        if self.running:
            self.notify(
                'Wait for the current turn to finish.',
                severity='warning',
            )
            return

        if len(self.messages) <= 1:
            self._write_note('There is nothing to compact yet.')
            return

        self._busy('Compacting conversation')
        self.compact_conversation()

    def _compaction_finished(self, changed, before, cost):
        self._mark_ready()

        if changed:
            self._write_note(
                f'Conversation compacted: '
                f'{before} -> {len(self.messages)} messages'
            )
        else:
            self._write_note('There is nothing to compact yet.')

        self._set_status(
            'Ready',
            f'${cost:.6f} compact'
            f'  |  ${llm.CONVERSATION_COST:.6f} total',
        )

    def _compaction_failed(self, error):
        self._mark_ready()
        self._set_status(
            'Ready after error',
            f'${llm.CONVERSATION_COST:.6f} conversation',
        )
        self._write_panel(
            'compaction error',
            Group(
                Text(
                    f'{type(error).__name__}: {error}',
                    style=f'bold {ERROR}',
                ),
                Text(''),
                Text(
                    'The conversation was not changed.',
                    style=MUTED,
                ),
            ),
            border=ERROR,
        )

    # ------------------------------------------------------------------
    # Actions and state
    # ------------------------------------------------------------------

    def action_new_chat(self):
        if self.running:
            self.notify(
                'Wait for the current turn to finish.',
                severity='warning',
            )
            return

        self.messages[:] = [
            {'role': 'system', 'content': build_system_prompt()},
        ]
        TODOS.clear()
        llm.CONVERSATION_COST = 0.0

        prompt = self.query_one('#prompt', Input)
        prompt.value = ''
        self.query_one('#transcript', RichLog).clear()
        self._set_status('Ready', '')
        self._welcome()
        prompt.focus()

    def action_focus_prompt(self):
        self.query_one('#prompt', Input).focus()

    def _busy(self, label):
        self.running = True
        self.query_one('#prompt', Input).disabled = True
        self._set_status(label, '')

    def _mark_ready(self):
        self.running = False
        prompt = self.query_one('#prompt', Input)
        prompt.disabled = False
        prompt.focus()

    def _set_status(self, status, usage):
        style = ERROR if 'error' in status.lower() else YELLOW
        self.query_one('#status', Static).update(
            Text(status, style=f'bold {style}')
        )
        self.query_one('#usage', Static).update(
            Text(usage, style=MUTED)
        )

    # ------------------------------------------------------------------
    # Transcript rendering
    # ------------------------------------------------------------------

    def _welcome(self):
        self._write_panel(
            'INIT AI Guild Coding Agent',
            Group(
                Text(
                    'A thin terminal frontend over the guild agent loop.',
                    style=MUTED,
                ),
                Text(''),
                Text('Try a task:', style=f'bold {YELLOW}'),
                Text(
                    '  Inspect this project and explain how it works.',
                    style=TEXT,
                ),
                Text(
                    '  Fix the failing test and rerun the relevant checks.',
                    style=TEXT,
                ),
                Text(''),
                Text(
                    'Commands: /help  /todos  /skills  /compact  /new',
                    style=MUTED,
                ),
            ),
            border=YELLOW,
        )

    def _write_user(self, content):
        self._write_panel(
            'you',
            Text(content, style='bold #ffffff'),
            border=YELLOW,
        )

    def _write_agent(self, content):
        self._write_panel(
            'agent',
            Markdown(content),
            border=ORANGE,
        )

    def _write_tool(self, data):
        name = data.get('name', 'tool')
        args = data.get('args') or {}

        if name == 'write_todos' and isinstance(args.get('todos'), list):
            self._write_todos(args['todos'])
            return

        result = data.get('result') or ''
        lines = result.strip().splitlines() or ['(no output)']
        shown = lines[:MAX_TOOL_LINES]
        hidden = len(lines) - len(shown)
        failed = _looks_like_error(result)

        result_text = Text(
            '\n'.join(shown),
            style=ERROR if failed else MUTED,
        )

        if hidden:
            result_text.append(
                f'\n... {hidden} more lines',
                style=f'italic {ORANGE}',
            )

        self._write_panel(
            f'tool  {name}',
            Group(
                _format_args(args),
                Text(''),
                result_text,
            ),
            border=ERROR if failed else MUTED,
        )

    def _write_todos(self, todos):
        if not todos:
            self._write_note('No todos.')
            return

        table = Table.grid(padding=(0, 1))
        table.add_column(no_wrap=True)
        table.add_column(overflow='fold')

        for todo in todos:
            status = todo.get('status', 'pending')
            content = todo.get('content', '')

            if status == 'in_progress':
                style = f'bold {YELLOW}'
            elif status == 'done':
                style = f'strike {MUTED}'
            else:
                style = TEXT

            table.add_row(
                Text(MARKS.get(status, '[?]'), style=style),
                Text(content, style=style),
            )

        done = sum(todo.get('status') == 'done' for todo in todos)
        self._write_panel(
            f'todos  {done}/{len(todos)}',
            table,
            border=ORANGE,
        )

    def _write_help(self):
        table = Table.grid(padding=(0, 2))
        table.add_column(no_wrap=True)
        table.add_column(overflow='fold')

        for command, description in COMMAND_ROWS:
            table.add_row(
                Text(command, style=f'bold {YELLOW}'),
                Text(description, style=TEXT),
            )

        self._write_panel('commands', table)

    def _write_skills(self):
        skills = list_skills()

        if not skills:
            self._write_note(
                'No skills found in .agents/skills. Add a '
                '<name>/SKILL.md directory to create one.'
            )
            return

        body = [Text(f'{len(skills)} available', style=MUTED), Text('')]
        body.extend(
            Text(f'- {skill}', style=TEXT)
            for skill in skills
        )
        body.extend([
            Text(''),
            Text(
                'The agent loads a matching skill with read_skill.',
                style=MUTED,
            ),
        ])

        self._write_panel('skills', Group(*body))

    def _write_model(self):
        model = os.environ.get('MODEL', 'MODEL is not configured')
        base_url = os.environ.get('BASE_URL', 'BASE_URL is not configured')

        self._write_panel(
            'model',
            Group(
                Text(model, style=f'bold {YELLOW}'),
                Text(base_url, style=MUTED),
            ),
        )

    def _write_note(self, content):
        self.query_one('#transcript', RichLog).write(
            Text(content, style=f'italic {MUTED}')
        )

    def _write_panel(self, title, content, border=MUTED):
        self.query_one('#transcript', RichLog).write(
            Panel(
                content,
                title=Text(title, style=f'bold {YELLOW}'),
                title_align='left',
                border_style=border,
                padding=(0, 1),
            )
        )

    @staticmethod
    def _context_text():
        model = os.environ.get('MODEL', 'not configured')
        skill_count = len(list_skills())
        skills = (
            f'{skill_count} available (/skills to list)'
            if skill_count
            else 'none'
        )

        return Text.assemble(
            ('MODEL   ', f'bold {YELLOW}'),
            (model, MUTED),
            ('\n', ''),
            ('CWD     ', f'bold {YELLOW}'),
            (_shorten_path(Path.cwd()), MUTED),
            ('\n', ''),
            ('SKILLS  ', f'bold {YELLOW}'),
            (skills, MUTED),
        )


def _shorten_path(path, limit=56):
    """Keep the useful tail of a long path inside the context bar."""
    text = str(path)
    home = str(Path.home())

    if text == home or text.startswith(home + os.sep):
        text = '~' + text[len(home):]

    if len(text) <= limit:
        return text

    tail = text[-(limit - 4):]

    for separator in ('\\', '/'):
        index = tail.find(separator)
        if index != -1:
            tail = tail[index + 1:]
            break

    return '...' + tail


def _looks_like_error(result):
    return result.startswith('Error:') or result.startswith('Exit code ')


def _format_args(args):
    if not args:
        return Text('(no arguments)', style=MUTED)

    if set(args) == {'command'}:
        return Text(f"$ {args['command']}", style=ORANGE)

    lines = []

    for key, value in args.items():
        if isinstance(value, str):
            rendered = value
        else:
            rendered = json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        if len(rendered) > MAX_ARG_CHARS:
            rendered = rendered[:MAX_ARG_CHARS] + '...'

        indented = rendered.replace('\n', '\n  ')
        lines.append(f'{key}: {indented}')

    return Text('\n'.join(lines), style=ORANGE)


def main():
    GuildAgentApp().run()


if __name__ == '__main__':
    main()
