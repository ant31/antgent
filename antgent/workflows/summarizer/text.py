import asyncio
import logging
import uuid
from datetime import timedelta

from agents.tracing import trace
from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from temporalio.common import RetryPolicy

    from antgent.agents.summarizer.logic import summarize_one_type
    from antgent.agents.summarizer.models import (
        InternalSummariesAllResult,
        InternalSummaryResult,
        SummaryInput,
        SummaryType,
    )
    from antgent.models.agent import AgentWorkflowOutput
    from antgent.models.visibility import WorkflowStepStatus
    from antgent.workflows.base import BaseWorkflow, WorkflowInput, heartbeat_every


logger = logging.getLogger(__name__)


@activity.defn
async def run_summarizer_one_type_activity(ctx: SummaryInput) -> InternalSummaryResult:
    """Activity to run the summarizer for one type."""
    async with heartbeat_every():
        group_id = uuid.uuid4().hex[:16]
        with trace(
            workflow_name=f"SummarizeOneType-{ctx.summary_type.value}",
            metadata={},
            group_id=group_id,
        ):
            return await summarize_one_type(ctx)


@workflow.defn
class TextSummarizerOneTypeWorkflow(BaseWorkflow[SummaryInput, InternalSummaryResult]):
    """Workflow to generate a single type of summary for a given text."""

    @workflow.run
    async def run(self, data: WorkflowInput[SummaryInput]) -> AgentWorkflowOutput[InternalSummaryResult]:
        self._init_run(data)
        ctx = data.agent_input.context
        self._update_status("Input Processing", WorkflowStepStatus.COMPLETED)

        self._update_status("Summarizing Text", WorkflowStepStatus.RUNNING)
        try:
            result = await workflow.execute_activity(
                run_summarizer_one_type_activity,
                ctx,
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(minutes=1),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            self.result = AgentWorkflowOutput(result=result, workflow_info=data.wid)
            self._update_status("Summarizing Text", WorkflowStepStatus.COMPLETED)
            self._update_status("Workflow End", WorkflowStepStatus.COMPLETED)
            return self.result
        except Exception:
            self._update_status("Summarizing Text", WorkflowStepStatus.FAILED)
            self._update_status("Workflow End", WorkflowStepStatus.FAILED)
            raise


@workflow.defn
class TextSummarizerAllWorkflow(BaseWorkflow[SummaryInput, InternalSummariesAllResult]):
    """Workflow to generate all available types of summaries for a given text, running them in parallel."""

    @workflow.run
    async def run(self, data: WorkflowInput[SummaryInput]) -> AgentWorkflowOutput[InternalSummariesAllResult]:
        self._init_run(data)
        ctx = data.agent_input.context
        self._update_status("Input Processing", WorkflowStepStatus.COMPLETED)
        self._update_status("Summarizing Text (Multi)", WorkflowStepStatus.RUNNING)

        try:
            summary_types: set[SummaryType] = set(SummaryType)
            tasks = []
            for summary_type in summary_types:
                task_ctx = ctx.model_copy(deep=True)
                task_ctx.summary_type = summary_type
                tasks.append(
                    workflow.execute_activity(
                        run_summarizer_one_type_activity,
                        task_ctx,
                        start_to_close_timeout=timedelta(minutes=5),
                        heartbeat_timeout=timedelta(minutes=1),
                        retry_policy=RetryPolicy(maximum_attempts=3),
                    )
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)

            validated_results: dict[SummaryType, InternalSummaryResult | None] = {}
            for res in results:
                if isinstance(res, Exception):
                    workflow.logger.error(f"A summarization activity failed: {res}", exc_info=True)
                elif res and res.summary_type:
                    validated_results[res.summary_type] = res

            result = InternalSummariesAllResult(summaries=validated_results)

            self.result = AgentWorkflowOutput(result=result, workflow_info=data.wid)
            self._update_status("Summarizing Text (Multi)", WorkflowStepStatus.COMPLETED)
            self._update_status("Workflow End", WorkflowStepStatus.COMPLETED)
            return self.result
        except Exception:
            self._update_status("Summarizing Text (Multi)", WorkflowStepStatus.FAILED)
            self._update_status("Workflow End", WorkflowStepStatus.FAILED)
            raise
