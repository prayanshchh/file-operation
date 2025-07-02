PROMPT_EXAMPLES = '''
# Example 1: Replace content in a Python file
[
  {
    "file": "main.py",
    "action": "replace",
    "content": "<new file content here>"
  }
]

# Example 2: Append to a README
[
  {
    "file": "README.md",
    "action": "append",
    "content": "<text to append>"
  }
]

# Example 3: Multiple edits
[
  {
    "file": "hello.txt",
    "action": "replace",
    "content": "<new file content>"
  },
  {
    "file": "requirements.txt",
    "action": "append",
    "content": "<text to append to requirements.txt>"
  }
]

# Example 4: Add a license header to all Python files
[
  {
    "file": "main.py",
    "action": "replace",
    "content": "<main.py with license header>"
  },
  {
    "file": "utils.py",
    "action": "replace",
    "content": "<utils.py with license header>"
  }
]

# Example 5: Append a changelog entry
[
  {
    "file": "CHANGELOG.md",
    "action": "append",
    "content": "<changelog entry to append>"
  }
]
''' 