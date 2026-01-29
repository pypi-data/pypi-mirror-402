from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any

from hooks.interfaces import CursorHooks

ENTRYPOINT_GROUP = "py_cursor_hooks.hooks"


def _coerce_to_hooks(obj: Any) -> CursorHooks:
    """
    Accept:
    - CursorHooks instance
    - CursorHooks subclass (instantiated with no args)
    """
    match obj:
        case CursorHooks():
            return obj
        case type() as cls if issubclass(cls, CursorHooks):
            return cls()
        case _:
            raise TypeError(
                "Entry point must be a CursorHooks instance or a CursorHooks subclass."
            )


def load_hooks() -> CursorHooks:
    """
    Load a CursorHooks implementation from entry points.

    Requires exactly one entry point registered in group `py_cursor_hooks.hooks`.
    """
    eps = list(entry_points().select(group=ENTRYPOINT_GROUP))
    if len(eps) == 1:
        return _coerce_to_hooks(eps[0].load())
    if len(eps) == 0:
        raise RuntimeError(
            f'No hook implementation found. Register an entry point in group "{ENTRYPOINT_GROUP}".'
        )
    raise RuntimeError(
        f'Multiple hook implementations found in entry point group "{ENTRYPOINT_GROUP}".'
    )
