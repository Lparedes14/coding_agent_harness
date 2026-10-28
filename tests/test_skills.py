from pathlib import Path

import pytest

from coding_agent.skills import list_skills, read_skill


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / '.agents' / 'skills'


def parse_frontmatter(text):
    assert text.startswith('---\n'), 'SKILL.md must start with YAML frontmatter'
    _, block, body = text.split('---', 2)

    fields = {}
    for line in block.strip().splitlines():
        key, separator, value = line.partition(':')
        assert separator, f'Invalid frontmatter line: {line!r}'
        fields[key.strip()] = value.strip()

    return fields, body


def test_every_skill_directory_is_discovered():
    on_disk = sorted(
        path.name
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / 'SKILL.md').exists()
    )

    assert on_disk
    assert list_skills() == on_disk


@pytest.mark.parametrize('name', list_skills())
def test_skill_has_valid_frontmatter_and_body(name):
    text = (SKILLS_DIR / name / 'SKILL.md').read_text(encoding='utf-8')
    fields, body = parse_frontmatter(text)

    assert fields['name'] == name
    assert fields['description']
    assert body.strip(), f'{name} has no instructions'
    assert body.lstrip().startswith('# '), f'{name} must start with a heading'


@pytest.mark.parametrize('name', list_skills())
def test_readme_lists_every_skill(name):
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')

    assert f'- `{name}`' in readme


def test_read_skill_returns_instructions():
    content = read_skill('debugging')

    assert content.startswith('---\nname: debugging')
    assert '# Debugging' in content


def test_read_skill_unknown_name_lists_available_skills():
    result = read_skill('does-not-exist')

    assert "skill 'does-not-exist' not found" in result
    for name in list_skills():
        assert name in result
