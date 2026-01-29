from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from hooks import models
from hooks.interfaces import CursorHooks
from hooks.models import HookEvent


@dataclass(frozen=True)
class HookSpec:
    input_model: type[models.BaseInput]
    output_model: type[models.BaseOutput]
    handler: Callable[[Any], models.BaseOutput]


def build_hook_table(impl: CursorHooks) -> dict[HookEvent, HookSpec]:
    return {
        HookEvent.beforeShellExecution: HookSpec(
            models.BeforeShellExecutionInput,
            models.BeforeExecutionOutput,
            impl.before_shell_execution,
        ),
        HookEvent.afterShellExecution: HookSpec(
            models.AfterShellExecutionInput,
            models.AfterShellExecutionOutput,
            impl.after_shell_execution,
        ),
        HookEvent.beforeMCPExecution: HookSpec(
            models.BeforeMCPExecutionInput,
            models.BeforeExecutionOutput,
            impl.before_mcp_execution,
        ),
        HookEvent.afterMCPExecution: HookSpec(
            models.AfterMCPExecutionInput,
            models.AfterMCPExecutionOutput,
            impl.after_mcp_execution,
        ),
        HookEvent.beforeReadFile: HookSpec(
            models.BeforeReadFileInput,
            models.BeforeReadFileOutput,
            impl.before_read_file,
        ),
        HookEvent.afterFileEdit: HookSpec(
            models.AfterFileEditInput,
            models.AfterFileEditOutput,
            impl.after_file_edit,
        ),
        HookEvent.beforeSubmitPrompt: HookSpec(
            models.BeforeSubmitPromptInput,
            models.BeforeSubmitPromptOutput,
            impl.before_submit_prompt,
        ),
        HookEvent.stop: HookSpec(models.StopInput, models.StopOutput, impl.stop),
        HookEvent.afterAgentResponse: HookSpec(
            models.AfterAgentResponseInput,
            models.AfterAgentResponseOutput,
            impl.after_agent_response,
        ),
        HookEvent.afterAgentThought: HookSpec(
            models.AfterAgentThoughtInput,
            models.AfterAgentThoughtOutput,
            impl.after_agent_thought,
        ),
        HookEvent.beforeTabFileRead: HookSpec(
            models.BeforeTabFileReadInput,
            models.BeforeTabFileReadOutput,
            impl.before_tab_file_read,
        ),
        HookEvent.afterTabFileEdit: HookSpec(
            models.AfterTabFileEditInput,
            models.AfterTabFileEditOutput,
            impl.after_tab_file_edit,
        ),
    }


def dispatch(
    *,
    hook_table: dict[HookEvent, HookSpec],
    raw_json: str,
    hook: HookEvent,
) -> models.BaseOutput:
    spec = hook_table.get(hook)
    if spec is None:
        raise ValueError(
            f"Unknown hook event: {hook.value}. "
            f"Supported: {', '.join(e.value for e in hook_table)}"
        )

    parsed_input = spec.input_model.model_validate_json(raw_json)
    return spec.handler(parsed_input)
