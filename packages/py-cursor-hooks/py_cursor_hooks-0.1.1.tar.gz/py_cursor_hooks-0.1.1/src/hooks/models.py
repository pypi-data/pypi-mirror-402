from enum import Enum
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CursorBaseModel(BaseModel):
    """
    Base model for Cursor hook payloads.

    - Forward compatible: ignore unknown fields.
    - Allows aliases (e.g. Attachment.filePath).
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


AttachmentType = Literal["file", "rule"]


class Attachment(CursorBaseModel):
    type: AttachmentType
    file_path: str = Field(validation_alias=AliasChoices("filePath", "file_path"))


class BaseInput(CursorBaseModel):
    conversation_id: str
    generation_id: str
    model: str | None = None
    hook_event_name: str
    cursor_version: str | None = None
    workspace_roots: list[str]
    user_email: str | None = None


class BaseOutput(CursorBaseModel):
    def to_json_line(self) -> str:
        """Serialize to JSON with trailing newline for stdout."""
        return self.model_dump_json(by_alias=True, exclude_none=True) + "\n"


# -------------------------
# Stop
# -------------------------


StopStatus = Literal["completed", "aborted", "error"]


class StopInput(BaseInput):
    status: StopStatus
    loop_count: int


class StopOutput(BaseOutput):
    followup_message: str | None = None


# -------------------------
# Before execution (Shell / MCP)
# -------------------------


Permission = Literal["allow", "deny", "ask"]


class BeforeShellExecutionInput(BaseInput):
    command: str
    cwd: str


class BeforeMCPExecutionInput(BaseInput):
    tool_name: str
    tool_input: str  # JSON string of params
    url: str | None = None
    command: str | None = None


class BeforeExecutionOutput(BaseOutput):
    permission: Permission
    user_message: str | None = None
    agent_message: str | None = None


# -------------------------
# After execution (Shell / MCP)
# -------------------------


class AfterShellExecutionInput(BaseInput):
    command: str
    output: str
    duration: int  # milliseconds


class AfterShellExecutionOutput(BaseOutput):
    pass


class AfterMCPExecutionInput(BaseInput):
    tool_name: str
    tool_input: str
    result_json: str
    duration: int  # milliseconds


class AfterMCPExecutionOutput(BaseOutput):
    pass


# -------------------------
# File access (Agent)
# -------------------------


class BeforeReadFileInput(BaseInput):
    file_path: str
    content: str
    attachments: list[Attachment] | None = None


class BeforeReadFileOutput(BaseOutput):
    permission: Permission
    user_message: str | None = None
    agent_message: str | None = None


class Edit(CursorBaseModel):
    old_string: str
    new_string: str


class AfterFileEditInput(BaseInput):
    file_path: str
    edits: list[Edit]


class AfterFileEditOutput(BaseOutput):
    pass


# -------------------------
# Prompt validation
# -------------------------


class BeforeSubmitPromptInput(BaseInput):
    prompt: str
    attachments: list[Attachment] | None = None


class BeforeSubmitPromptOutput(BaseOutput):
    # Named continue_ because "continue" is a Python reserved keyword.
    # Serializes as "continue" in JSON via the alias.
    continue_: bool = Field(alias="continue")
    user_message: str | None = None


class AfterAgentResponseInput(BaseInput):
    text: str


class AfterAgentResponseOutput(BaseOutput):
    pass


class AfterAgentThoughtInput(BaseInput):
    text: str
    duration_ms: int | None = Field(default=None, alias="duration_ms")


class AfterAgentThoughtOutput(BaseOutput):
    pass


# -------------------------
# Tab hooks (inline completions)
# -------------------------


class BeforeTabFileReadInput(BaseInput):
    file_path: str
    content: str


class BeforeTabFileReadOutput(BaseOutput):
    permission: Literal["allow", "deny"]


class EditRange(CursorBaseModel):
    start_line_number: int
    start_column: int
    end_line_number: int
    end_column: int


class TabEdit(CursorBaseModel):
    old_string: str
    new_string: str
    range: EditRange
    old_line: str
    new_line: str


class AfterTabFileEditInput(BaseInput):
    file_path: str
    edits: list[TabEdit]


class AfterTabFileEditOutput(BaseOutput):
    pass


# -------------------------
# Registry helpers
# -------------------------


class HookEvent(str, Enum):
    beforeShellExecution = "beforeShellExecution"
    afterShellExecution = "afterShellExecution"
    beforeMCPExecution = "beforeMCPExecution"
    afterMCPExecution = "afterMCPExecution"
    beforeReadFile = "beforeReadFile"
    afterFileEdit = "afterFileEdit"
    beforeSubmitPrompt = "beforeSubmitPrompt"
    stop = "stop"
    afterAgentResponse = "afterAgentResponse"
    afterAgentThought = "afterAgentThought"
    beforeTabFileRead = "beforeTabFileRead"
    afterTabFileEdit = "afterTabFileEdit"
