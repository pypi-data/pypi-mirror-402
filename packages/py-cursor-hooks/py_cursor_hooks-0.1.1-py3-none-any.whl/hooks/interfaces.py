from hooks import models


class CursorHooks:
    """
    Class-based, type-safe Cursor hooks interface.

    Subclass this and override any hook methods you care about.
    The default implementations are safe no-ops / allow-by-default.
    """

    # -------------------------
    # Agent hooks
    # -------------------------

    def before_shell_execution(
        self,
        _input: models.BeforeShellExecutionInput,
    ) -> models.BeforeExecutionOutput:
        return models.BeforeExecutionOutput(permission="allow")

    def after_shell_execution(
        self,
        _input: models.AfterShellExecutionInput,
    ) -> models.AfterShellExecutionOutput:
        return models.AfterShellExecutionOutput()

    def before_mcp_execution(
        self,
        _input: models.BeforeMCPExecutionInput,
    ) -> models.BeforeExecutionOutput:
        return models.BeforeExecutionOutput(permission="allow")

    def after_mcp_execution(
        self,
        _input: models.AfterMCPExecutionInput,
    ) -> models.AfterMCPExecutionOutput:
        return models.AfterMCPExecutionOutput()

    def before_read_file(
        self,
        _input: models.BeforeReadFileInput,
    ) -> models.BeforeReadFileOutput:
        return models.BeforeReadFileOutput(permission="allow")

    def after_file_edit(
        self,
        _input: models.AfterFileEditInput,
    ) -> models.AfterFileEditOutput:
        return models.AfterFileEditOutput()

    def before_submit_prompt(
        self,
        _input: models.BeforeSubmitPromptInput,
    ) -> models.BeforeSubmitPromptOutput:
        return models.BeforeSubmitPromptOutput(continue_=True)

    def stop(self, _input: models.StopInput) -> models.StopOutput:
        return models.StopOutput()

    def after_agent_response(
        self,
        _input: models.AfterAgentResponseInput,
    ) -> models.AfterAgentResponseOutput:
        return models.AfterAgentResponseOutput()

    def after_agent_thought(
        self,
        _input: models.AfterAgentThoughtInput,
    ) -> models.AfterAgentThoughtOutput:
        return models.AfterAgentThoughtOutput()

    # -------------------------
    # Tab hooks
    # -------------------------

    def before_tab_file_read(
        self,
        _input: models.BeforeTabFileReadInput,
    ) -> models.BeforeTabFileReadOutput:
        return models.BeforeTabFileReadOutput(permission="allow")

    def after_tab_file_edit(
        self,
        _input: models.AfterTabFileEditInput,
    ) -> models.AfterTabFileEditOutput:
        return models.AfterTabFileEditOutput()
