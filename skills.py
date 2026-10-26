from pathlib import Path

SKILLS_DIR = Path('.agents/skills')


def list_skills():
    return sorted(path.parent.name for path in SKILLS_DIR.glob('*/SKILL.md'))

def read_skill(name: str) -> str:
    if name not in list_skills():
        return f"Error: skill `{name}` does not exist"

    return (SKILLS_DIR / name / 'SKILL.md').read_text()