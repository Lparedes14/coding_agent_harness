from pathlib import Path

SKILLS_DIR = Path('.agents/skills')


def read_skill(name: str) -> str:
    ...