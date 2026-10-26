import json
import os

from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, RichLog, Static

from . import llm
from .agent import HELP, build_system_prompt, compact_history, run_agent
from .skills import list_skills
from .tools import MARKS, TODOS


YELLOW = '#ffd21c'
ORANGE = '#ffb000'
BLACK = '#080808'
SURFACE = '#151515'
MUTED = '#8b8b8b'
MAX_TOOL_LINES = 12


class GuildAgentApp(App):
    TITLE = 'INIT AI Guild Coding Agent'
    SUB_TITLE = os.environ.get('MODEL', 'model not configured')

    CSS = f"""
    Screen {{
        background: {BLACK};
        color: #f5f5f5;
    }}

    Header {{
        background: {YELLOW};
        color: {BLACK};
        text-style: bold;
    }}

    #context {{
        height: 4;
        padding: 1 2;
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

    #status {{
        height: 1;
        padding: 0 2;
        background: {SURFACE};
        color: {YELLOW};
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
        yield Static(
            Text.assemble(
                ('model  ', f'bold {YELLOW}'),
                (os.environ.get('MODEL', 'not configured'), MUTED),
                ('    directory  ', f'bold {YELLOW}'),
                (os.getcwd(), MUTED),
            ),
            id='context',
        )
        yield RichLog(
            id='transcript',
            wrap=True,
            highlight=False,
            markup=False,
        )
        yield Static('Ready', id='status')
        yield Input(
            placeholder='Ask the Guild agent…  (/help for commands)',
            id='prompt',
        )
        yield Footer()

    def on_mount(self):
        self._welcome()
        self.query_one('#prompt', Input).focus()

    @on(Input.Submitted)
    def submit(self, event: Input.Submitted):
        text = event.value.strip()

        if not text or self.running:
            return

        event.input.value = ''

        if text.startswith('/'):
            self._command(text.lower())
            return

        self._write_user(text)
        self.messages.append({'role': 'user', 'content': text})
        self._busy('Thinking…')
        self.run_turn()

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
            self.call_from_thread(self._failed, error)
            return

        turn_cost = llm.CONVERSATION_COST - starting_cost
        self.call_from_thread(self._finished, usage, turn_cost)

    @work(thread=True, exclusive=True, exit_on_error=False)
    def compact_conversation(self):
        starting_cost = llm.CONVERSATION_COST

        try:
            before = len(self.messages)
            changed = compact_history(self.messages)
        except Exception as error:
            self.call_from_thread(self._failed, error)
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
        elif kind == 'tool':
            self._write_tool(data)
        elif kind == 'compacted':
            self._write_note(
                f"Conversation compacted: "
                f"{data['before']} → {data['after']} messages"
            )
        elif kind == 'note':
            self._write_note(data['content'])

    def _command(self, command):
        if command in {'/quit', '/exit'}:
            self.exit()
        elif command == '/help':
            self._write_panel('commands', Text(HELP, style=MUTED))
        elif command == '/new':
            self.action_new_chat()
        elif command == '/compact':
            self._busy('Compacting…')
            self.compact_conversation()
        elif command == '/todos':
            self._write_todos(TODOS)
        elif command == '/skills':
            skills = list_skills()
            body = '\n'.join(f'• {skill}' for skill in skills)
            self._write_panel(
                'skills',
                Text(body or 'No skills found.', style=MUTED),
            )
        elif command == '/model':
            self._write_note(
                os.environ.get('MODEL', 'MODEL is not configured')
            )
        else:
            self._write_note(f'Unknown command: {command}')

    def action_new_chat(self):
        if self.running:
            return

        self.messages[:] = [
            {'role': 'system', 'content': build_system_prompt()},
        ]
        TODOS.clear()
        llm.CONVERSATION_COST = 0.0
        self.query_one('#transcript', RichLog).clear()
        self.query_one('#status', Static).update('Ready')
        self._welcome()

    def action_focus_prompt(self):
        self.query_one('#prompt', Input).focus()

    def _busy(self, label):
        self.running = True
        prompt = self.query_one('#prompt', Input)
        prompt.disabled = True
        self.query_one('#status', Static).update(f'● {label}')

    def _finished(self, usage, turn_cost):
        self.running = False
        prompt = self.query_one('#prompt', Input)
        prompt.disabled = False
        prompt.focus()

        self.query_one('#status', Static).update(
            f"Ready  •  {usage['prompt_tokens']:,} prompt  •  "
            f"{usage['completion_tokens']:,} completion  •  "
            f"${turn_cost:.6f} turn  •  "
            f"${llm.CONVERSATION_COST:.6f} conversation"
        )

    def _failed(self, error):
        self.running = False
        prompt = self.query_one('#prompt', Input)
        prompt.disabled = False
        prompt.focus()
        self.query_one('#status', Static).update('Ready after error')
        self._write_panel(
            'error',
            Text(f'{type(error).__name__}: {error}', style='bold red'),
            border='red',
        )

    def _compaction_finished(self, changed, before, cost):
        self.running = False
        prompt = self.query_one('#prompt', Input)
        prompt.disabled = False
        prompt.focus()

        if changed:
            self._write_note(
                f'Conversation compacted: '
                f'{before} → {len(self.messages)} messages'
            )
        else:
            self._write_note('There is nothing to compact yet.')

        self.query_one('#status', Static).update(
            f'Ready  •  ${cost:.6f} compact  •  '
            f'${llm.CONVERSATION_COST:.6f} conversation'
        )

    def _welcome(self):
        self._write_panel(
            'INIT AI Guild Coding Agent',
            Group(
                Text(
                    'Tools, skills, subagents, TODOs, and compaction are ready.',
                    style=MUTED,
                ),
            ),
            border=YELLOW,
        )

    def _write_user(self, content):
        self._write_panel(
            'you',
            Text(content, style='bold white'),
            border=YELLOW,
        )

    def _write_agent(self, content):
        self._write_panel(
            'agent',
            Markdown(content),
            border=ORANGE,
        )

    def _write_tool(self, data):
        name = data['name']
        args = data['args']

        if name == 'write_todos' and isinstance(args.get('todos'), list):
            self._write_todos(args['todos'])
            return

        lines = data['result'].strip().splitlines() or ['(no output)']
        shown = lines[:MAX_TOOL_LINES]
        hidden = len(lines) - len(shown)
        result = Text('\n'.join(shown), style=MUTED)

        if hidden:
            result.append(
                f'\n… {hidden} more lines',
                style=f'italic {ORANGE}',
            )

        self._write_panel(
            f'tool  {name}',
            Group(
                Text(self._format_args(args), style=ORANGE),
                result,
            ),
            border=MUTED,
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
            style = MUTED

            if status == 'in_progress':
                style = f'bold {YELLOW}'
            elif status == 'done':
                style = f'strike {MUTED}'

            table.add_row(
                Text(MARKS.get(status, '[?]'), style=style),
                Text(todo.get('content', ''), style=style),
            )

        done = sum(todo.get('status') == 'done' for todo in todos)
        self._write_panel(
            f'todos  {done}/{len(todos)}',
            table,
            border=ORANGE,
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
    def _format_args(args):
        if len(args) == 1:
            value = next(iter(args.values()))
            return value if isinstance(value, str) else json.dumps(value)
        return json.dumps(args, ensure_ascii=False)


def main():
    GuildAgentApp().run()


if __name__ == '__main__':
    main()
