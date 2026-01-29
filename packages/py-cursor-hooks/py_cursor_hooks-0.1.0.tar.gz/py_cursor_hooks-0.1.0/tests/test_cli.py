"""Tests for CLI input handling."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from hooks.main import app

runner = CliRunner()


class TestCliIntegration:
    """Integration tests for the CLI."""

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

        with patch("hooks.main.load_hooks") as mock_load:
            from hooks.interfaces import CursorHooks

            mock_load.return_value = CursorHooks()

            result = runner.invoke(app, ["--hook", "stop"], input=json_input)

            assert result.exit_code == 0
            output = json.loads(result.stdout.strip())
            assert output == {}

    def test_cli_errors_on_invalid_json(self) -> None:
        with patch("hooks.main.load_hooks") as mock_load:
            from hooks.interfaces import CursorHooks

            mock_load.return_value = CursorHooks()

            result = runner.invoke(app, ["--hook", "stop"], input="not valid json")

            assert result.exit_code != 0

    def test_cli_errors_on_unknown_hook(self) -> None:
        json_input = json.dumps(
            {
                "conversation_id": "c",
                "generation_id": "g",
                "workspace_roots": [],
            }
        )

        with patch("hooks.main.load_hooks") as mock_load:
            from hooks.interfaces import CursorHooks

            mock_load.return_value = CursorHooks()

            result = runner.invoke(app, ["--hook", "fakeHook"], input=json_input)

            assert result.exit_code != 0

    def test_cli_requires_hook_option(self) -> None:
        """--hook is required."""
        result = runner.invoke(app, input="{}")
        assert result.exit_code != 0
        assert "--hook" in result.output
