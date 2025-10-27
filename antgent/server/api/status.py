import logging
from typing import Annotated

import temporalio.client
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from temporalio.client import Client

from antgent.temporal.client import tclient

logger = logging.getLogger(__name__)


async def get_workflow_status(workflow_id: str, client: Client) -> dict:
    """Generic workflow status poller."""
    try:
        handle = client.get_workflow_handle(workflow_id)
        describe = await handle.describe()
    except Exception as e:
        raise HTTPException(status_code=404, detail={"error": "Workflow not found.", "workflow_id": workflow_id}) from e

    if describe.status == temporalio.client.WorkflowExecutionStatus.FAILED:
        try:
            # This is not guaranteed to have the failure.
            failure_result = await handle.result(timeout=1.0)
            failure_str = str(failure_result)
        except Exception:
            failure_str = "Unknown failure"
        raise HTTPException(
            status_code=500,
            detail={"error": "Workflow has failed.", "details": failure_str, "workflow_id": workflow_id},
        )
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
            response_data = progress.model_dump(mode="json")
        elif isinstance(progress, dict):
            response_data = progress
        else:
            response_data = {"progress_details": progress}

        response_data["workflow_status"] = describe.status.name
        return response_data
    except Exception as e:
        logger.warning("Could not query progress for workflow %s, it might be an old version: %s", workflow_id, e)
        # Fallback for older workflows that might fail on progress query
        return {
            "workflow_status": describe.status.name,
            "status_timeline": [("Query", "failed")],
            "error": (
                f"Failed to query workflow progress, it might be an older version. Status is {describe.status.name}."
            ),
            "workflow_id": workflow_id,
        }


router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


@router.get("/status/{workflow_id}")
async def workflow_status(workflow_id: str, client: Annotated[Client, Depends(tclient)]) -> dict:
    """Polls for the status and results of any workflow execution."""
    return await get_workflow_status(workflow_id, client)
