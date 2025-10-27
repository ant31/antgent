import asyncio
import logging
import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from temporalio.client import Client

from antgent.agents.summarizer.models import SummariesResult, SummaryInput, SummaryOutput
from antgent.models.agent import (
    AgentTextSummariesWorkflowOutput,
    AgentTextSummaryWorkflowOutput,
)
from antgent.models.visibility import WorkflowInfo
from antgent.server.api.status import get_workflow_status
from antgent.temporal.client import tclient
from antgent.temporal.queue_manager import get_workflow_queue
from antgent.workflows.base import WorkflowInput
from antgent.workflows.summarizer.text import (
    TextSummarizerAllWorkflow,
    TextSummarizerOneTypeWorkflow,
)

router = APIRouter(prefix="/api/workflows", tags=["Summarizer"])

logger = logging.getLogger(__name__)


@router.post("/summarizer/sync", tags=["sync"])
async def text_summarize(
    ctx: WorkflowInput[SummaryInput], client: Annotated[Client, Depends(tclient)]
) -> AgentTextSummaryWorkflowOutput:
    """Executes a single-type summarization workflow and waits for the result."""
    workflow_id = f"summarizer-one-type-sync-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerOneTypeWorkflow.__name__)
    queue = get_workflow_queue()

    handle = await client.start_workflow(
        TextSummarizerOneTypeWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    try:
        timeout_seconds = timedelta(minutes=5).total_seconds()
        result_output = await asyncio.wait_for(handle.result(), timeout=timeout_seconds)

        summary_output: SummaryOutput | None = None
        if result_output.result:
            summary_output = result_output.result.summary

        return AgentTextSummaryWorkflowOutput(
            result=summary_output,
            workflow_info=result_output.workflow_info,
            cost=result_output.cost,
            metadata=result_output.metadata,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Workflow did not complete within the specified timeout",
                "workflow_id": workflow_id,
                "timeout": timeout_seconds,
            },
        ) from exc


@router.post("/summarizer-multi", tags=["sync"], deprecated=True, summary="Re-added for backward compatibility")
@router.post("/summarizer-multi/sync", tags=["sync"])
async def text_summarize_all(
    ctx: WorkflowInput[SummaryInput], client: Annotated[Client, Depends(tclient)]
) -> AgentTextSummariesWorkflowOutput:
    """Executes a multi-type summarization workflow and waits for the results."""
    if ctx.agent_input.context.iterations > 3:
        logger.warning("Maximum iterations is reduced to 3")
        ctx.agent_input.context.iterations = 3

    workflow_id = f"summarizer-all-sync-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerAllWorkflow.__name__)
    queue = get_workflow_queue()

    handle = await client.start_workflow(
        TextSummarizerAllWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    try:
        timeout_seconds = timedelta(minutes=10).total_seconds()
        result_output = await asyncio.wait_for(handle.result(), timeout=timeout_seconds)

        summaries_all_result = result_output.result
        summaries_result = None
        if summaries_all_result and summaries_all_result.summaries:
            summaries_dict = {
                s_type: s_result.summary if s_result else None
                for s_type, s_result in summaries_all_result.summaries.items()
            }
            summaries_result = SummariesResult(summaries=summaries_dict)

        return AgentTextSummariesWorkflowOutput(
            result=summaries_result,
            workflow_info=result_output.workflow_info,
            cost=result_output.cost,
            metadata=result_output.metadata,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Workflow did not complete within the specified timeout",
                "workflow_id": workflow_id,
                "timeout": timeout_seconds,
            },
        ) from exc


@router.post("/summarizer/run", tags=["async"])
async def run_summarizer_one_type(
    ctx: WorkflowInput[SummaryInput], client: Annotated[Client, Depends(tclient)]
) -> dict[str, str]:
    """Starts a text summarizer workflow for a single type and returns the workflow ID."""
    workflow_id = f"summarizer-one-type-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerOneTypeWorkflow.__name__)
    queue = get_workflow_queue()
    await client.start_workflow(
        TextSummarizerOneTypeWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    return {"workflow_id": workflow_id}


@router.get("/summarizer/{workflow_id}/status", tags=["async"])
async def summarizer_one_type_status(workflow_id: str, client: Annotated[Client, Depends(tclient)]) -> dict:
    """Polls for the status and results of a TextSummarizerOneTypeWorkflow execution."""
    return await get_workflow_status(workflow_id, client)


@router.post("/summarizer/retrigger_async", tags=["async"])
async def summarizer_one_type_retrigger(
    ctx: WorkflowInput[SummaryInput], client: Annotated[Client, Depends(tclient)]
) -> dict[str, str]:
    """Retriggers a TextSummarizerOneTypeWorkflow with the same input and returns the new workflow_id."""
    workflow_id = f"summarizer-one-type-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerOneTypeWorkflow.__name__)
    queue = get_workflow_queue()
    await client.start_workflow(
        TextSummarizerOneTypeWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    return {"workflow_id": workflow_id}


@router.post("/summarizer-all/run", tags=["async"])
async def run_summarizer_all(
    ctx: WorkflowInput[SummaryInput], client: Annotated[Client, Depends(tclient)]
) -> dict[str, str]:
    """Starts a text summarizer workflow for all types and returns the workflow ID."""
    workflow_id = f"summarizer-all-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerAllWorkflow.__name__)
    queue = get_workflow_queue()
    await client.start_workflow(
        TextSummarizerAllWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    return {"workflow_id": workflow_id}


@router.get("/summarizer-all/{workflow_id}/status", tags=["async"])
async def summarizer_all_status(workflow_id: str, client: Annotated[Client, Depends(tclient)]) -> dict:
    """Polls for the status and results of a TextSummarizerAllWorkflow execution."""
    return await get_workflow_status(workflow_id, client)


@router.post("/summarizer-all/retrigger_async", tags=["async"])
async def summarizer_all_retrigger(
    ctx: WorkflowInput[SummaryInput], client: Annotated[Client, Depends(tclient)]
) -> dict[str, str]:
    """Retriggers a TextSummarizerAllWorkflow with the same input and returns the new workflow_id."""
    workflow_id = f"summarizer-all-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerAllWorkflow.__name__)
    queue = get_workflow_queue()
    await client.start_workflow(
        TextSummarizerAllWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    return {"workflow_id": workflow_id}
