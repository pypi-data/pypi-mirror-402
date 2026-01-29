import argparse
import sys
from typing import TextIO

from hooks import models
from hooks.loader import load_hooks
from hooks.runner import build_hook_table, dispatch


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a Cursor hook.")
    parser.add_argument(
        "--hook",
        required=True,
        choices=[event.value for event in models.HookEvent],
        help="Hook event name (e.g. beforeShellExecution).",
    )
    return parser


def run_hook(
    hook: models.HookEvent,
    *,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run a Cursor hook with JSON input from stdin."""
    try:
        hooks_impl = load_hooks()
        hook_table = build_hook_table(hooks_impl)

        raw = stdin.read()
        out_model = dispatch(hook_table=hook_table, raw_json=raw, hook=hook)

        stdout.write(out_model.to_json_line())
    except Exception as exc:  # noqa: BLE001
        stderr.write(f"{exc}\n")
        return 1

    return 0


def main() -> int:
    """Run a Cursor hook with JSON input from stdin."""
    parser = _build_parser()

    args = parser.parse_args()

    return run_hook(
        models.HookEvent(args.hook),
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    sys.exit(main())
