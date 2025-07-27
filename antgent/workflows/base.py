import asyncio
import contextlib
from typing import Any, TypeVar

from pydantic import BaseModel
from temporalio import activity, workflow

from antgent.config import config
from antgent.models.agent import AgentConfig, AgentWorkflowInput, AgentWorkflowOutput, WorkflowInfo
from antgent.models.visibility import WorkflowProgress, WorkflowStepStatus

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


class BaseWorkflowInput[TInput](BaseModel):
    agent_conf: dict[str, AgentConfig] | None = None
    agent_input: AgentWorkflowInput[TInput]


class BaseWorkflow[TInput, TResult]:
    """A base class for Temporal workflows to standardize progress tracking."""

    def __init__(self):
        self.agentsconf = config().agents
        self.status_timeline: dict[str, WorkflowStepStatus] = {}
        self.input_ctx: TInput | None = None
        self.result: AgentWorkflowOutput[TResult] | None = None
        self.data: BaseWorkflowInput[TInput] | None = None

    def _init_run(self, data: BaseWorkflowInput[TInput]) -> None:
        """Initializes the workflow run with the provided input data."""
        self.data = data
        self.input_ctx = data.agent_input.context
        self.data.agent_input.wid = WorkflowInfo(
            name=workflow.info().workflow_type,
            wid=workflow.info().workflow_id,
            namespace=workflow.info().namespace,
            run_id=workflow.info().run_id,
        )
        if self.data.agent_conf is not None:
            self.agentsconf = self.data.agent_conf

        self._update_status("Workflow Start", WorkflowStepStatus.RUNNING)

    @workflow.run
    async def run(self, data: BaseWorkflowInput[TInput]) -> AgentWorkflowOutput[TResult]:
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
