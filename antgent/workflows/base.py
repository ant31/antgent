import asyncio
import contextlib
import warnings
from typing import Any, TypeVar

from pydantic import BaseModel, Field
from temporalio import activity, workflow

from antgent.aliases import Aliases, AliasResolver
from antgent.config import config
from antgent.models.agent import AgentConfig, AgentInput, AgentWorkflowOutput, DynamicAgentConfig
from antgent.models.visibility import Visibility, WorkflowInfo, WorkflowProgress, WorkflowStepStatus

# type WInput[TInput] = BaseWorkflowInput[TInput]
TInput = TypeVar("TInput")
TResult = TypeVar("TResult")


@contextlib.asynccontextmanager
async def heartbeat_every(delay: int = 30):
    """An async context manager to send heartbeats periodically."""

    async def _heartbeat_in_background():
        """Periodically sends heartbeats."""
        while True:
            activity.heartbeat()
            await asyncio.sleep(delay)

    heartbeat_task = asyncio.create_task(_heartbeat_in_background())
    try:
        yield
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task


@activity.defn
async def demo_activity_with_heartbeat() -> int:
    """Activity to run the reply grading workflow."""
    async with heartbeat_every():
        return 1


class WorkflowInput[TInput](BaseModel):
    """
    Input structure for workflows with clear separation of concerns:
    - agent_input: The agent's input data (context + llm_input)
    - agent_config: Optional runtime configuration overrides
    - wid: Workflow identification and metadata
    - visibility: Workflow visibility and tracing information
    """

    agent_input: AgentInput[TInput] = Field(..., description="The agent's input data (context and llm_input)")
    agent_config: DynamicAgentConfig | None = Field(
        default=None, description="Optional runtime configuration for agents (models, aliases)"
    )
    wid: WorkflowInfo = Field(default_factory=WorkflowInfo, description="The ID and metadata of the temporal workflow")
    visibility: Visibility = Field(
        default_factory=Visibility, description="The visibility information for the agent workflow run"
    )


# Backwards compatibility alias with deprecation warning
def _deprecated_wf_input_warning():
    warnings.warn(
        "BaseWorkflowInput is deprecated and will be removed in version 1.0.0. Use WorkflowInput instead.",
        DeprecationWarning,
        stacklevel=3,
    )


class BaseWorkflowInput[TInput](WorkflowInput[TInput]):
    """
    Deprecated: Use WorkflowInput instead.

    This class is kept for backwards compatibility and will be removed in version 1.0.0.
    """

    def __init__(self, **data):
        _deprecated_wf_input_warning()
        super().__init__(**data)


class BaseWorkflow[TInput, TResult]:
    """A base class for Temporal workflows to standardize progress tracking."""

    def __init__(self):
        self.agentsconf = config().agents
        self.status_timeline: dict[str, WorkflowStepStatus] = {}
        self.input_ctx: TInput | None = None
        self.result: AgentWorkflowOutput[TResult] | None = None
        self.data: WorkflowInput[TInput] | None = None
        self.alias_resolver: AliasResolver = Aliases

    def _init_run(self, data: WorkflowInput[TInput]) -> None:
        """Initializes the workflow run with the provided input data."""
        self.data = data
        self.input_ctx = data.agent_input.context
        self.data.wid = WorkflowInfo(
            name=workflow.info().workflow_type,
            wid=workflow.info().workflow_id,
            namespace=workflow.info().namespace,
            run_id=workflow.info().run_id,
        )

        # Apply dynamic configuration if provided
        if data.agent_config is not None:
            self.agentsconf = self._apply_dynamic_config(data.agent_config)

        self.data.visibility.steps.start_time = workflow.now()
        self._update_status("Workflow Start", WorkflowStepStatus.RUNNING)

    def _apply_dynamic_config(self, dynamic_config: DynamicAgentConfig) -> dict[str, AgentConfig]:
        """
        Applies dynamic configuration overrides for this workflow run.

        Precedence:
        1. agent_config.agents[name] (most specific)
        2. agent_config.model (global override)
        3. self.agentsconf (default from config)
        """
        # Start with existing configuration
        result_config = dict(self.agentsconf)

        # Merge aliases if provided, creating a temporary resolver for this run
        if dynamic_config.aliases:
            # Start with a copy of global aliases
            merged_aliases = dict(Aliases)
            # Update with run-specific aliases
            merged_aliases.update(dynamic_config.aliases)
            self.alias_resolver = AliasResolver(merged_aliases)

        # Apply global model override to all agents
        if dynamic_config.model:
            for _agent_name, agent_config in result_config.items():
                agent_config.model = dynamic_config.model

        # Apply per-agent overrides (most specific) - ONLY model name
        for agent_name, model_info in dynamic_config.agents.items():
            if agent_name not in result_config:
                result_config[agent_name] = AgentConfig(name=agent_name)

            # Update ONLY the model field
            result_config[agent_name].model = model_info.model

        return result_config

    @workflow.run
    async def run(self, data: WorkflowInput[TInput]) -> AgentWorkflowOutput[TResult]:
        """Runs the workflow with the provided input data."""
        self._init_run(data)
        raise NotImplementedError("Subclasses must implement the run method.")

    def _update_status(self, step: str, status: WorkflowStepStatus) -> None:
        """Updates the status of a given step in the timeline."""
        self.status_timeline[step] = status

    @workflow.query
    def get_progress(self) -> WorkflowProgress[TInput, TResult]:
        """Returns the standardized progress of the workflow."""
        return WorkflowProgress(
            status_timeline=self.status_timeline,
            input=self.input_ctx,
            result=self.result.result if self.result else None,
            intermediate_results=self._get_intermediate_results(),
        )

    def _get_intermediate_results(self) -> dict[str, Any]:
        """
        Returns a dictionary of intermediate results.
        Subclasses can override this to provide specific data.
        """
        return {}
