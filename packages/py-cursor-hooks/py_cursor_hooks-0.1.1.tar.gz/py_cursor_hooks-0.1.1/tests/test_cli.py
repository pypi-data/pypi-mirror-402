"""Tests for CLI input handling."""

import contextlib
import io
import json
import sys
from unittest.mock import patch

from hooks import models, run


class TestCliIntegration:
    """Integration tests for the CLI."""

    def _invoke_run_hook(
        self, hook: models.HookEvent, input_text: str
    ) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO(input_text)
        exit_code = run.run_hook(
            hook,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def _invoke_main(self, args: list[str], input_text: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        stdin = io.StringIO(input_text)
        with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            original_argv = sys.argv
            original_stdin = sys.stdin
            sys.argv = ["run", *args]
            sys.stdin = stdin
            try:
                exit_code = run.main()
            except SystemExit as exc:
                exit_code = int(exc.code) if exc.code is not None else 1
            finally:
                sys.argv = original_argv
                sys.stdin = original_stdin
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_cli_reads_from_stdin(self) -> None:
        json_input = json.dumps(
            {
                "hook_event_name": "stop",
                "conversation_id": "c",
                "generation_id": "g",
                "workspace_roots": [],
                "status": "completed",
                "loop_count": 0,
            }
        )

        with patch("hooks.run.load_hooks") as mock_load:
            from hooks.interfaces import CursorHooks

            mock_load.return_value = CursorHooks()

            exit_code, output, _ = self._invoke_run_hook(
                models.HookEvent.stop,
                json_input,
            )

            assert exit_code == 0
            output = json.loads(output.strip())
            assert output == {}

    def test_cli_errors_on_invalid_json(self) -> None:
        with patch("hooks.run.load_hooks") as mock_load:
            from hooks.interfaces import CursorHooks

            mock_load.return_value = CursorHooks()

            exit_code, _, _ = self._invoke_run_hook(
                models.HookEvent.stop,
                "not valid json",
            )

            assert exit_code != 0

    def test_cli_errors_on_unknown_hook(self) -> None:
        json_input = json.dumps(
            {
                "conversation_id": "c",
                "generation_id": "g",
                "workspace_roots": [],
            }
        )

        with patch("hooks.run.load_hooks") as mock_load:
            from hooks.interfaces import CursorHooks

            mock_load.return_value = CursorHooks()

            exit_code, _, _ = self._invoke_main(["--hook", "fakeHook"], json_input)

            assert exit_code != 0

    def test_cli_requires_hook_option(self) -> None:
        """--hook is required."""
        exit_code, _, stderr = self._invoke_main([], "{}")
        assert exit_code != 0
        assert "--hook" in stderr
