# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=too-few-public-methods
import logging

import temporalio.client
from ant31box.server.exception import ResourceNotFound
from fastapi import APIRouter

from antgent.models.job import AsyncResponse
from antgent.temporal.utils import get_handler

router = APIRouter(prefix="/api/job", tags=["antgent", "status"])

logger = logging.getLogger(__name__)


@router.post("/status")
async def status(ar: AsyncResponse, with_result: bool = False) -> AsyncResponse:
    """
    Retrieve the status of the workflow and update the AsyncResponse object.

    :param ar: The AsyncResponse object containing the job details.
    :return: The updated AsyncResponse object with the workflow status and result.
    """
    for job in ar.payload.jobs:
        workflow_id = job.uuid
        handler, _ = await get_handler(workflow_id=job.uuid, workflow_name=job.name)
        describe = await handler.describe()
        j = job
        if not describe.status:
            raise ResourceNotFound("Workflow not found", {"message": "Workflow not found", "workflow_id": workflow_id})
        j.status = describe.status.name
        ## Don't include result. Add new endpoint for result if needed
        if (
            describe.status == temporalio.client.WorkflowExecutionStatus.COMPLETED
            and with_result
            and ar.secret_key
            and ar.check_signature()
        ):
            j.result = await handler.result()

    ar.gen_signature()
    return ar
