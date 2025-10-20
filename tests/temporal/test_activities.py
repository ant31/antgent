import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.testing import ActivityEnvironment
from temporalio.worker import Worker

from antgent.temporal.activities import AnyData, aecho, echo
from antgent.temporal.workflows.echo import EchoAsyncWorkflow, EchoWorkflow

logger = logging.getLogger(__name__)

# A list of tuples where each tuple contains:
# - The activity function
# - The order amount
# - The expected result string
activity_test_data = [
    ({"works": None, "echo": True} ),
    ({"pages": ["a", "b"], "parts": 3} ),
]
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data", activity_test_data
)
async def test_echo_activity(data):
    activity_environment = ActivityEnvironment()
    model = AnyData(**data)
    result = activity_environment.run(echo, model)
    assert result.model_dump() == data



async def test_echo_workflow(client: Client):
    task_queue_name = str(uuid.uuid4())
    logger.info(client.data_converter)
    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[EchoWorkflow],
        activities=[echo],
        activity_executor=ThreadPoolExecutor(10),
    ):
        assert (await client.execute_workflow(
            EchoWorkflow.run,
            AnyData(**{'Hello': "World!"}),
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
            run_timeout=timedelta(seconds=3),

        )).model_dump()['Hello'] == "World!"


async def test_aecho_workflow(client: Client):
    task_queue_name = str(uuid.uuid4())

    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[EchoAsyncWorkflow],
        activities=[aecho],
    ):
        res = (await client.execute_workflow(
            EchoAsyncWorkflow.run,
            {'Hello': "World!"},
            id=str(uuid.uuid4()),
            task_queue=task_queue_name,
            run_timeout=timedelta(seconds=3),
        ))
        assert 'Hello' in res
        assert res['Hello'] == "World!"




@activity.defn(name="aecho")
async def aecho_mocked(model: dict[str, Any]) -> dict[str, Any]:
    _ = model
    return {"greeting": "Hello from mocked activity!"}


async def test_mock_activity(client: Client):
    task_queue_name = str(uuid.uuid4())
    async with Worker(
        client,
        task_queue=task_queue_name,
        activity_executor=ThreadPoolExecutor(10),
        workflows=[EchoAsyncWorkflow],
        activities=[aecho_mocked],
    ):
        assert (await client.execute_workflow(
            EchoAsyncWorkflow.run,
            {'ignore': "World"},
            id=str(uuid.uuid4()),
            run_timeout=timedelta(seconds=3),
            task_queue=task_queue_name,
        ))['greeting'] == "Hello from mocked activity!"
