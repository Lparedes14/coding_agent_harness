import sys

from coding_agent import tools


def test_bash_returns_output():
    command = f'"{sys.executable}" -c "print(\'workshop-ok\')"'

    assert tools.bash(command) == 'workshop-ok'


def test_bash_reports_nonzero_exit_code():
    command = f'"{sys.executable}" -c "raise SystemExit(7)"'

    assert tools.bash(command) == 'Exit code 7\nNo output'


def test_bash_preserves_failure_output():
    command = (
        f'"{sys.executable}" -c '
        '"import sys; print(\'broken\', file=sys.stderr); raise SystemExit(3)"'
    )

    assert tools.bash(command) == 'Exit code 3\nbroken'


def test_bash_preserves_spaces_and_separates_streams():
    command = (
        f'"{sys.executable}" -c '
        '"import sys; sys.stdout.write(\'  output  \'); '
        'sys.stderr.write(\'error\')"'
    )

    assert tools.bash(command) == '  output  \nerror'


def test_file_tools(tmp_path):
    path = tmp_path / 'example.txt'

    assert tools.write_file(str(path), 'alpha beta') == f'Wrote {path}'
    assert tools.read_file(str(path)) == 'alpha beta'
    assert tools.edit_file(str(path), 'beta', 'gamma') == (
        f'Replaced 1 match(es) in {path}'
    )
    assert tools.read_file(str(path)) == 'alpha gamma'
    assert tools.edit_file(str(path), '', 'unused').startswith('Error:')


def test_todos_allow_only_one_active_item():
    valid = [
        {
            'content': 'Inspect the code',
            'activeForm': 'Inspecting the code',
            'status': 'in_progress',
        },
        {
            'content': 'Run tests',
            'activeForm': 'Running tests',
            'status': 'pending',
        },
    ]
    invalid = [
        {**valid[0], 'content': 'First'},
        {**valid[0], 'content': 'Second'},
    ]

    try:
        assert '[~] Inspect the code' in tools.write_todos(valid)
        assert tools.write_todos(invalid).startswith('Error: 2 tasks')
    finally:
        tools.TODOS.clear()
