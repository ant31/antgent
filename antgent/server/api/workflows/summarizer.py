import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from temporalio.client import Client

from antgent.models.visibility import WorkflowInfo
from antgent.temporal.client import tclient
from antgent.workflows.base import WorkflowInput
from antgent.workflows.summarizer import TextSummarizerWorkflow
from antgent.workflows.summarizer.models import (
    TextSummarizerWorkflowContext,
)

from ..utils import get_workflow_queue

router = APIRouter(prefix="/api/workflows", tags=["Summarizer"])

logger = logging.getLogger(__name__)


async def _get_workflow_status(workflow_id: str) -> dict:
    """Generic workflow status poller."""
    client: Client = await tclient()
    try:
        handle = client.get_workflow_handle(workflow_id)
        describe = await handle.describe()
    except Exception as e:
        raise HTTPException(status_code=404, detail={"error": "Workflow not found.", "workflow_id": workflow_id}) from e

    if not describe.status:
        raise HTTPException(
            status_code=404,
            detail={
                "status_timeline": [("Error", "not_found")],
                "error": "Workflow not found.",
                "workflow_id": workflow_id,
            },
        )

    try:
        progress = await handle.query("get_progress")
        if isinstance(progress, BaseModel):
            return progress.model_dump(mode="json")
        return progress
    except Exception as e:
        logger.warning(f"Could not query progress for workflow {workflow_id}, it might be an old version: {e}")
        # Fallback for older workflows that might fail on progress query
        return {
            "status_timeline": [("Query", "failed")],
            "error": (
                f"Failed to query workflow progress, it might be an older version. Status is {describe.status.name}."
            ),
            "workflow_id": workflow_id,
        }


@router.post("/summarizer")
async def run_summarizer(
    workflow_input: WorkflowInput[TextSummarizerWorkflowContext],
) -> dict[str, str]:
    """Starts a text summarizer workflow and returns the workflow ID."""
    client = await tclient()
    workflow_id = f"summarizer-{uuid.uuid4().hex}"

    # Set the workflow info
    workflow_input.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerWorkflow.__name__)

    queue = get_workflow_queue()

    await client.start_workflow(
        TextSummarizerWorkflow.run,
        workflow_input,
        id=workflow_id,
        task_queue=queue,
    )

    return {"workflow_id": workflow_id}


@router.get("/summarizer/{workflow_id}")
async def summarizer_status(workflow_id: str) -> dict:
    """Polls for the status and results of a TextSummarizerWorkflow execution."""
    return await _get_workflow_status(workflow_id)


@router.post("/summarizer/retrigger")
async def summarizer_retrigger_api(
    workflow_input: WorkflowInput[TextSummarizerWorkflowContext],
) -> dict[str, str]:
    """Retriggers a TextSummarizerWorkflow and returns the new workflow_id."""
    client: Client = await tclient()
    workflow_id = f"summarizer-{uuid.uuid4().hex}"

    workflow_input.wid = WorkflowInfo(wid=workflow_id, name=TextSummarizerWorkflow.__name__)

    queue = get_workflow_queue()

    await client.start_workflow(
        TextSummarizerWorkflow.run,
        workflow_input,
        id=workflow_id,
        task_queue=queue,
    )

    return {"workflow_id": workflow_id}
