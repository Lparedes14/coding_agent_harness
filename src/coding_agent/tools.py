import subprocess

def bash(command: str) -> str:
    # Code
    pass

def read_file(file_path: str) -> str:
    # Code
    pass

def write_file(file_path: str, content: str) -> str:
    # Code
    pass

def edit_file(file_path: str, old_str: str, new_str: str, allow_multi_edit=False):
    # Code
    pass

MARKS = {'pending': '[ ]', 'in_progress': '[~]', 'done': '[X]'}
TODOS = []
def write_todos(todos):
    active = [todo for todo in todos if todo['status'] == 'in_progress']
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress"
    
    TODOS[:] = todos
    return '\n'.join(
        f"{MARKS[todo['status']]} {todo['content']}" for todo in TODOS
    ) or "Todo list cleared"



TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its combined stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run",
                    }
                },
                "required": ["command"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    }
                },
                "required": ["file_path"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, replacing the file if it already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write",
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Edit a file by replacing an exact string with a new string. "
                "By default, fails if the old string appears more than once."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit",
                    },
                    "old_str": {
                        "type": "string",
                        "description": "Exact text to find in the file",
                    },
                    "new_str": {
                        "type": "string",
                        "description": "Text that will replace old_str",
                    },
                    "allow_multi_edit": {
                        "type": "boolean",
                        "description": (
                            "Whether to replace all matches if old_str appears multiple times"
                        ),
                        "default": False,
                    },
                },
                "required": ["file_path", "old_str", "new_str"],
            },
        },
    },

    {"type": "function",
    "function": {
        "name": "write_todos",
        "description": (
            "Record the plan for a multi-step task. Send the whole list every "
            "time. Keep exactly one task in_progress and update it as you go."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The task, imperative: 'Fix the parser'",
                            },
                            "activeForm": {
                                "type": "string",
                                "description": "Present continuous: 'Fixing the parser'",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "done"],
                            },
                        },
                        "required": ["content", "activeForm", "status"],
                    },
                }
            },
            "required": ["todos"],
        },
    },
    },
]

TOOLS = {
    'bash': bash,
    'read_file': read_file,
    'write_file': write_file,
    'edit_file': edit_file,
    'write_todos': write_todos,
}