import sys
from typing import Annotated

import typer

from hooks import models
from hooks.loader import load_hooks
from hooks.runner import build_hook_table, dispatch

app = typer.Typer(add_completion=False)


@app.command()
def run(
    *,
    hook: Annotated[
        models.HookEvent,
        typer.Option("--hook", help="Hook event name (e.g. beforeShellExecution)."),
    ],
) -> None:
    """Run a Cursor hook with JSON input from stdin."""
    hooks_impl = load_hooks()
    hook_table = build_hook_table(hooks_impl)

    raw = sys.stdin.read()
    out_model = dispatch(hook_table=hook_table, raw_json=raw, hook=hook)

    sys.stdout.write(out_model.to_json_line())


if __name__ == "__main__":
    app()
