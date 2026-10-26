from pathlib import Path

SKILLS_DIR = Path('.agents/skills')


def list_skills():
    # TODO(WORKSHOP 2)
    ...

def read_skill(name: str) -> str:
    # TODO(WORKSHOP 2)
    ...

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