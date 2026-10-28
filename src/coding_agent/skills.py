from pathlib import Path

SKILLS_DIR = Path('.agents/skills')


def list_skills():
    if not SKILLS_DIR.exists():
        return []

    return sorted(
        path.name
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / 'SKILL.md').exists()
    )


def read_skill(name: str) -> str:
    path = SKILLS_DIR / name / 'SKILL.md'

    if not path.exists():
        return f"Error: skill '{name}' not found. Available: {', '.join(list_skills()) or 'none'}"

    return path.read_text(encoding='utf-8')


READ_SKILL_SCHEMA = {
    'type': 'function',
    'function': {
        'name': 'read_skill',
        'description': 'Read the complete instructions for an available skill.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the skill to load',
                },
            },
            'required': ['name'],
        },
    },
}