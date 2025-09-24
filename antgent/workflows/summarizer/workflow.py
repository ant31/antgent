import asyncio
import contextlib
import logging
import uuid
from datetime import timedelta

from agents.tracing import trace
from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

with workflow.unsafe.imports_passed_through():
    from temporalio.common import RetryPolicy

    from antgent.agents.summarizer.models import SummaryResult
    from antgent.agents.summarizer.summary import SummaryAgent
    from antgent.config import config
    from antgent.models.agent import AgentWorkflowOutput
    from antgent.models.visibility import WorkflowStepStatus
    from antgent.workflows.base import BaseWorkflow, BaseWorkflowInput
    from antgent.workflows.summarizer.models import TextSummarizerWorkflowContext

logger = logging.getLogger(__name__)


async def _heartbeat_in_background():
    """Periodically sends heartbeats."""
    while True:
        activity.heartbeat()
        await asyncio.sleep(30)


async def _summarize_logic(ctx: TextSummarizerWorkflowContext) -> SummaryResult:
    """Helper function to run summarization logic."""
    agentsconf = config().agents
    summarize_agent = SummaryAgent(conf=agentsconf)

    summary = await summarize_agent.workflow(llm_input="", context=ctx)
    if summary is None:
        raise ApplicationError("No summary generated")

    result = SummaryResult(summary=summary)
    return result


@activity.defn
async def run_summarizer_activity(ctx: TextSummarizerWorkflowContext) -> SummaryResult:
    """Activity to run the summarizer."""
    heartbeat_task = asyncio.create_task(_heartbeat_in_background())
    try:
        group_id = uuid.uuid4().hex[:16]
        with trace(
            workflow_name="Summarize",
            metadata={},
            group_id=group_id,
        ):
            return await _summarize_logic(ctx)
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task


@workflow.defn
class TextSummarizerWorkflow(BaseWorkflow[TextSummarizerWorkflowContext, SummaryResult]):
    def __init__(self) -> None:
        super().__init__()

    @workflow.run
    async def run(self, data: BaseWorkflowInput[TextSummarizerWorkflowContext]) -> AgentWorkflowOutput[SummaryResult]:
        self._init_run(data)
        ctx = data.agent_input.context
        self._update_status("Input Processing", WorkflowStepStatus.COMPLETED)

        self._update_status("Summarizing Text", WorkflowStepStatus.RUNNING)
        try:
            result = await workflow.execute_activity(
                run_summarizer_activity,
                ctx,
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            self.result = AgentWorkflowOutput(result=result, workflow_info=data.agent_input.wid)
            self._update_status("Summarizing Text", WorkflowStepStatus.COMPLETED)
            self._update_status("Workflow End", WorkflowStepStatus.COMPLETED)
            return self.result
        except Exception:
            self._update_status("Summarizing Text", WorkflowStepStatus.FAILED)
            self._update_status("Workflow End", WorkflowStepStatus.FAILED)
            raise
