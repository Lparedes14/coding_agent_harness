# Guild Coding Agent

A small coding-agent harness used for two AI Guild workshops. The agent can
inspect and edit files, run shell commands, maintain a TODO plan, load skills,
compact long conversations, and delegate read-only exploration to a subagent.

## Setup

Use Python 3.10 or newer. With `uv`, setup is:

```bash
uv sync --extra dev
cp .env.example .env
```

Or use a regular virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

Fill in `BASE_URL`, `OPENROUTER_API_KEY`, and `MODEL` in `.env`, then run:

```bash
uv run coding-agent
```

If you activated the regular virtual environment instead, run `coding-agent`
directly. The package form works too:

```bash
uv run python -m coding_agent
```

Run the CLI from the root of the project you want the agent to edit—normally
this cloned repository during the workshop. The agent reads `.env` and
`.agents/skills/` from that working directory.

## Commands

- `/help` shows available commands.
- `/new` starts a fresh conversation.
- `/compact` summarizes the current conversation.
- `/todos` displays the current plan.
- `/skills` lists available skills.
- `/model` shows the configured model.
- `/quit` exits.

## Tests

```bash
uv run pytest
```

Or run `pytest` directly from an activated virtual environment. The automated
tests mock all model responses and do not use API credits.

## Safety

This workshop project intentionally does not implement permissions or a shell
sandbox. The agent can execute commands and overwrite files. Run it in a
disposable clone and review important changes before keeping them.
