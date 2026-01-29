"""Comprehensive tests for all hook types and their default behaviors."""

import json

import pytest

from hooks import interfaces, models
from hooks.models import HookEvent
from hooks.runner import build_hook_table, dispatch


class TestDefaultHookBehaviors:
    """Test that default CursorHooks implementations return expected values."""

    def setup_method(self) -> None:
        self.hooks = interfaces.CursorHooks()
        self.table = build_hook_table(self.hooks)

    def _base_payload(self, hook_name: str) -> dict[str, object]:
        return {
            "hook_event_name": hook_name,
            "conversation_id": "test-conv",
            "generation_id": "test-gen",
            "workspace_roots": ["/workspace"],
        }

    def test_before_shell_execution_allows_by_default(self) -> None:
        payload = self._base_payload("beforeShellExecution")
        payload["command"] = "echo hello"
        payload["cwd"] = "/workspace"

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.beforeShellExecution,
        )

        assert isinstance(out, models.BeforeExecutionOutput)
        assert out.permission == "allow"

    def test_after_shell_execution_returns_empty(self) -> None:
        payload = self._base_payload("afterShellExecution")
        payload["command"] = "echo hello"
        payload["output"] = "hello\n"
        payload["duration"] = 100

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.afterShellExecution,
        )

        assert isinstance(out, models.AfterShellExecutionOutput)
        assert out.to_json_line() == "{}\n"

    def test_before_mcp_execution_allows_by_default(self) -> None:
        payload = self._base_payload("beforeMCPExecution")
        payload["tool_name"] = "read_file"
        payload["tool_input"] = '{"path": "/file.txt"}'

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.beforeMCPExecution,
        )

        assert isinstance(out, models.BeforeExecutionOutput)
        assert out.permission == "allow"

    def test_after_mcp_execution_returns_empty(self) -> None:
        payload = self._base_payload("afterMCPExecution")
        payload["tool_name"] = "read_file"
        payload["tool_input"] = '{"path": "/file.txt"}'
        payload["result_json"] = '{"content": "file contents"}'
        payload["duration"] = 50

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.afterMCPExecution,
        )

        assert isinstance(out, models.AfterMCPExecutionOutput)
        assert out.to_json_line() == "{}\n"

    def test_before_read_file_allows_by_default(self) -> None:
        payload = self._base_payload("beforeReadFile")
        payload["file_path"] = "/workspace/src/main.py"
        payload["content"] = "print('hello')"

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.beforeReadFile,
        )

        assert isinstance(out, models.BeforeReadFileOutput)
        assert out.permission == "allow"

    def test_after_file_edit_returns_empty(self) -> None:
        payload = self._base_payload("afterFileEdit")
        payload["file_path"] = "/workspace/src/main.py"
        payload["edits"] = [{"old_string": "foo", "new_string": "bar"}]

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.afterFileEdit,
        )

        assert isinstance(out, models.AfterFileEditOutput)
        assert out.to_json_line() == "{}\n"

    def test_before_submit_prompt_continues_by_default(self) -> None:
        payload = self._base_payload("beforeSubmitPrompt")
        payload["prompt"] = "Write a function to calculate fibonacci"

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.beforeSubmitPrompt,
        )

        assert isinstance(out, models.BeforeSubmitPromptOutput)
        assert out.continue_ is True

    def test_stop_continues_by_default(self) -> None:
        payload = self._base_payload("stop")
        payload["status"] = "completed"
        payload["loop_count"] = 5

        out = dispatch(
            hook_table=self.table, raw_json=json.dumps(payload), hook=HookEvent.stop
        )

        assert isinstance(out, models.StopOutput)
        assert out.followup_message is None

    def test_after_agent_response_returns_empty(self) -> None:
        payload = self._base_payload("afterAgentResponse")
        payload["text"] = "I've completed the task."

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.afterAgentResponse,
        )

        assert isinstance(out, models.AfterAgentResponseOutput)
        assert out.to_json_line() == "{}\n"

    def test_after_agent_thought_returns_empty(self) -> None:
        payload = self._base_payload("afterAgentThought")
        payload["text"] = "Let me analyze this..."

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.afterAgentThought,
        )

        assert isinstance(out, models.AfterAgentThoughtOutput)
        assert out.to_json_line() == "{}\n"

    def test_before_tab_file_read_allows_by_default(self) -> None:
        payload = self._base_payload("beforeTabFileRead")
        payload["file_path"] = "/workspace/src/utils.py"
        payload["content"] = "def helper(): pass"

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.beforeTabFileRead,
        )

        assert isinstance(out, models.BeforeTabFileReadOutput)
        assert out.permission == "allow"

    def test_after_tab_file_edit_returns_empty(self) -> None:
        payload = self._base_payload("afterTabFileEdit")
        payload["file_path"] = "/workspace/src/utils.py"
        payload["edits"] = []

        out = dispatch(
            hook_table=self.table,
            raw_json=json.dumps(payload),
            hook=HookEvent.afterTabFileEdit,
        )

        assert isinstance(out, models.AfterTabFileEditOutput)
        assert out.to_json_line() == "{}\n"


class TestModelValidation:
    """Test Pydantic model validation edge cases."""

    def test_base_input_ignores_unknown_fields(self) -> None:
        """Forward compatibility: unknown fields are ignored."""
        data = {
            "conversation_id": "c",
            "generation_id": "g",
            "hook_event_name": "test",
            "workspace_roots": [],
            "future_field": "should be ignored",
        }
        model = models.BaseInput.model_validate(data)
        assert model.conversation_id == "c"
        assert not hasattr(model, "future_field")

    def test_attachment_accepts_camel_case(self) -> None:
        """Alias support for filePath -> file_path."""
        data = {"type": "file", "filePath": "/path/to/file"}
        att = models.Attachment.model_validate(data)
        assert att.file_path == "/path/to/file"

    def test_attachment_accepts_snake_case(self) -> None:
        data = {"type": "file", "file_path": "/path/to/file"}
        att = models.Attachment.model_validate(data)
        assert att.file_path == "/path/to/file"

    def test_before_submit_prompt_output_serializes_continue_as_alias(self) -> None:
        """The continue_ field should serialize as 'continue'."""
        output = models.BeforeSubmitPromptOutput(continue_=True)
        data = output.model_dump(by_alias=True)
        assert "continue" in data
        assert data["continue"] is True


class TestDispatchEdgeCases:
    """Test dispatch function edge cases."""

    def setup_method(self) -> None:
        self.hooks = interfaces.CursorHooks()
        self.table = build_hook_table(self.hooks)

    def test_dispatch_raises_on_missing_hook(self) -> None:
        """Error when hook is not in table."""
        # Create an empty table to simulate missing hook
        empty_table: dict[HookEvent, object] = {}
        with pytest.raises(ValueError, match="Unknown hook event"):
            dispatch(hook_table=empty_table, raw_json="{}", hook=HookEvent.stop)  # type: ignore[arg-type]
