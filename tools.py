import subprocess

def bash(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=60
    )
    return (result.stdout + result.stderr) or "No Output"

def read_file(file_path: str) -> str:
    with open(file_path) as f:
        return f.read()

def write_file(file_path: str, content: str) -> str:
    with open(file_path) as f:
        f.write(content)
    return f"Wrote {file_path}"

def edit_file(file_path: str, old_str: str, new_str: str, allow_multi_edit=False):
    with open(file_path) as f:
        content = f.read()

    count = content.count(old_str)
    if count == 0:
        return f"Error: `old_str` was not found in {file_path}"
    if count > 1 and not allow_multi_edit:
        return f"Error: `old_str` matches {count} times in {file_path}"
    
    with open(file_path, 'w') as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} match(es) in {file_path}"


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

]

TOOLS = {
    'bash': bash,
    'read_file': read_file,
    'write_file': write_file,
    'edit_file': edit_file
}