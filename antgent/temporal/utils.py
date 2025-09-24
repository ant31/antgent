import asyncio
import logging
from collections.abc import Awaitable
from datetime import timedelta
from typing import Any

import temporalio.client
from temporalio.client import WorkflowHandle
from temporalio.service import RPCError, RPCStatusCode

from antgent.models.job import Job
from antgent.temporal.client import tclient
from antgent.utils.importpy import import_from_string

FuncType = Awaitable
WorkflowHandlerType = temporalio.client.WorkflowHandle[Any, Any]

logger = logging.getLogger(__name__)


async def get_handler(
    workflow_id: str,
    workflow_name: str | None,
) -> tuple[WorkflowHandlerType, Any]:
    """
    Retrieve the workflow handler and workflow object for the given workflow ID and name.

    :param workflow_id: The ID of the workflow.
    :param workflow_name: The name of the workflow.
    :return: A tuple containing the workflow handler and workflow object.
    """

    workflow = import_from_string(workflow_name)
    logger.debug("Retrieved workflow: %s, id: %s, name: %s", workflow, workflow_id, workflow_name)
    # Retrieve running workflow handler
    client = await tclient()
    return (
        client.get_workflow_handle_for(workflow_id=workflow_id, workflow=workflow.run),
        workflow,
    )


async def is_workflow_running(handler: WorkflowHandlerType) -> bool:
    """
    Check if the given workflow is running.
    """
    try:
        # Try to update the workflow
        describe = await handler.describe()
    except RPCError as exc:
        # If it fails because the workflow is not found or already completed,
        # create a new one
        if exc.status != RPCStatusCode.NOT_FOUND:
            logger.error("unexpected error: %s", exc)
            # Do not raise create a new workflow
            # raise exc
        logger.debug("Not running: Workflow not found: %s", handler.id)
        return False
    describe = await handler.describe()
    if describe.status != temporalio.client.WorkflowExecutionStatus.RUNNING:
        logger.debug("Not running: Workflow found: %s (%s)", handler.id, describe.status)
        return False
    return True


async def wait_for_result(
    workflow_name: str,
    handler: WorkflowHandle[Any, Any],
    wait: bool = False,
    timeout: int = 60,
    root_key: str | None = None,
) -> Job:
    results = {}
    if wait:
        try:
            res = await asyncio.wait_for(handler.result(rpc_timeout=timedelta(seconds=timeout)), timeout=timeout)
            if root_key:
                results[root_key] = res.model_dump()
            else:
                results = res.model_dump()
        except TimeoutError:
            pass
    status = "UNKNOWN"
    workflow_status = (await handler.describe()).status
    if workflow_status is not None:
        status = workflow_status.name

    return Job(uuid=handler.id, name=workflow_name, status=status, result=results)
