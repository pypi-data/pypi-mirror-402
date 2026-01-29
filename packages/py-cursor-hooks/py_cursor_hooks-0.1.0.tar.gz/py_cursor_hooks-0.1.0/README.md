# py-cursor-hooks

A typed Python Library for building [Cursor hooks](https://cursor.com/docs/agent/hooks).

## Why use this?

Cursor runs hooks as subprocesses and communicates via JSON on stdin/stdout. Without this SDK, you'd need to write shell scripts that manually parse JSON, validate inputs, and format responses. With it, you get to write Python and:

- **Pydantic models** for all hook inputs and outputs
- **Type-safe interfaces** that catch errors before runtime
- **A CLI** that works out of the box with Cursor

## Quick Start

### 1. Install

```bash
uv add py-cursor-hooks
```

### 2. Write your hooks

Create a module with your hook implementations:

```python
from hooks.interfaces import CursorHooks
from hooks.models import BeforeReadFileInput, BeforeReadFileOutput


class MyHooks(CursorHooks):
    def before_read_file(
        self, input: BeforeReadFileInput
    ) -> BeforeReadFileOutput:
        # Block reading .env files
        if input.file_path.endswith(".env"):
            return BeforeReadFileOutput(
                permission="deny",
                user_message="Cannot read .env files",
                agent_message="Reading .env files is not allowed",
            )
        return BeforeReadFileOutput(permission="allow")


hooks = MyHooks()
```

### 3. Register your hooks

In your `pyproject.toml`, add an entry point so the CLI can find your implementation:

```toml
[project.entry-points."py_cursor_hooks.hooks"]
default = "my_package.my_hooks:hooks"
```

Then install your project:

```bash
uv pip install -e .
```

### 4. Configure Cursor

Add your hooks to `~/.cursor/hooks.json`:

```json
{
  "version": 1,
  "hooks": {
    "beforeReadFile": [{ "command": "cursor-hooks --hook beforeReadFile" }]
  }
}
```

That's it! Cursor will now run your hooks automatically.
