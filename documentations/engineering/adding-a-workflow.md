# How to Add a New Agent Workflow

Workflows are the heart of the antgent system, orchestrating agents and other tasks to perform complex, long-running operations. They are built on [Temporal.io](https://temporal.io/), which makes them durable, reliable, and scalable.

This guide will walk you through creating a new workflow, orchestrating agents within it, tracking its progress, and exposing it through the API. We will use the `TextSummarizerWorkflow` as a point of reference for best practices.

## 1. Core Concepts

### Workflows
A workflow is a Python class that defines a sequence of steps. It's decorated with `@workflow.defn` and has a main entry point method decorated with `@workflow.run`. Our framework provides a `BaseWorkflow` class that includes built-in progress tracking and status reporting.

### Activities
Workflow code itself is deterministic and cannot perform I/O operations like network calls or file system access directly. Any non-deterministic code, such as calling an agent (which involves an LLM API call), database access, or calling external services, must be executed within an **Activity**.

Activities are simple Python functions decorated with `@activity.defn`. They are executed by Temporal workers and can be retried automatically on failure.

## 2. Creating a New Workflow

Let's create a hypothetical `DocumentProcessorWorkflow` that receives a document, summarizes it using a `SummaryAgent`, and returns the result.

### Step 1: Define Input and Output Models

First, define the Pydantic models for your workflow's context (input) and final result (output). This is typically done in a `models.py` file within your workflow's directory (e.g., `antgent/workflows/doc_processor/models.py`).

```python
# antgent/workflows/doc_processor/models.py
from antgent.agents.summarizer.models import SummaryInput, SummaryResult

class DocProcessorCtx(SummaryInput):
    # Inherit from SummaryInput and add any extra fields if needed
    pass

class DocProcessorResult(SummaryResult):
    # Inherit from SummaryResult
    pass
```

### Step 2: Create an Activity to Run the Agent

Now, create the activity that will execute your agent. This is typically placed in the same file as the workflow.

**Best Practice:** An activity should be a thin wrapper around an agent's `.workflow()` call. Heartbeating is handled automatically for long-running activities.

```python
# antgent/workflows/doc_processor/workflow.py
from temporalio import activity, exceptions
from antgent.agents.summarizer.summary import SummaryAgent
from .models import DocProcessorCtx, DocProcessorResult

@activity.defn
async def run_summarizer_activity(ctx: DocProcessorCtx) -> DocProcessorResult:
    """Activity to run the summarizer agent."""
    agent = SummaryAgent()
    res = await agent.workflow(llm_input="", context=ctx)
    if res is None:
        raise exceptions.ApplicationError("Summarizer agent returned None", non_retryable=True)
    return DocProcessorResult(summary=res)
```

### Step 3: Implement the Workflow Class

Now, assemble the activities in your workflow's `run` method. Our `BaseWorkflow` provides helpers for tracking progress.

-   `self._init_run(data)`: Initializes the workflow run and progress tracking.
-   `self._update_status(...)`: Updates the status of a step in the workflow's execution graph. This is visible via the API.
-   `workflow.execute_activity()`: Used to run an activity.

```python
# antgent/workflows/doc_processor/workflow.py
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from antgent.models.agent import AgentWorkflowOutput
from antgent.workflows.base import BaseWorkflow, BaseWorkflowInput
from antgent.models.visibility import WorkflowStepStatus
from .models import DocProcessorCtx, DocProcessorResult
# ... other imports

@workflow.defn
class DocumentProcessorWorkflow(BaseWorkflow[DocProcessorCtx, DocProcessorResult]):
    def __init__(self) -> None:
        super().__init__()

    @workflow.run
    async def run(self, data: BaseWorkflowInput[DocProcessorCtx]) -> AgentWorkflowOutput[DocProcessorResult]:
        self._init_run(data)
        ctx = data.agent_input.context
        self._update_status("Workflow Start", WorkflowStepStatus.COMPLETED)

        self._update_status("Summarization", WorkflowStepStatus.RUNNING)
        retry_policy = RetryPolicy(maximum_attempts=3)
        
        summary_result = await workflow.execute_activity(
            run_summarizer_activity,
            ctx,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )
        
        self._update_status("Summarization", WorkflowStepStatus.COMPLETED)
        
        self.result = AgentWorkflowOutput(result=summary_result, workflow_info=data.agent_input.wid)
        self._update_status("Workflow End", WorkflowStepStatus.COMPLETED)
        return self.result
```

### Step 4: Register the Workflow and Activities

For Temporal to recognize your new workflow and activities, you must register them in `antgent/config.py` within the `TemporalCustomConfigSchema`.

```python
# antgent/config.py
from pydantic import Field
from temporalloop.config_loader import TemporalConfigSchema, WorkerConfigSchema

class TemporalCustomConfigSchema(TemporalConfigSchema):
    workers: list[WorkerConfigSchema] = Field(
        default=[
            # ... other worker configs
            WorkerConfigSchema(
                name="antgent-workflow",
                queue="antgent-queue",
                activities=[],
                workflows=[
                    # ... other workflows
                    "antgent.workflows.doc_processor.workflow:DocumentProcessorWorkflow",
                ],
            ),
            WorkerConfigSchema(
                name="antgent-activities",
                queue="antgent-queue-activity",
                activities=[
                    # ... other activities
                    "antgent.workflows.doc_processor.workflow:run_summarizer_activity",
                ],
                workflows=[],
            ),
        ],
    )
    # ...
```

## 3. Exposing the Workflow via API

To make your workflow accessible, you need to create API endpoints.

### Step 1: Create an API Router

Create a new file, for example, `antgent/server/api/workflows/doc_processor.py`.

### Step 2: Implement the API Endpoints

You typically need two endpoints: one to start the workflow and one to check its status.

```python
# antgent/server/api/workflows/doc_processor.py
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from temporalio.client import Client
from antgent.models.agent import AgentWorkflowInput, WorkflowInfo
from antgent.temporal.client import tclient
from antgent.server.api.utils import get_workflow_queue
# Import your workflow class and context model
from antgent.workflows.doc_processor.workflow import DocumentProcessorWorkflow
from antgent.workflows.doc_processor.models import DocProcessorCtx

router = APIRouter(prefix="/api/workflows", tags=["DocProcessor"])

@router.post("/doc-processor")
async def run_doc_processor(ctx: DocProcessorCtx) -> dict[str, str]:
    """Starts a DocumentProcessorWorkflow and returns the workflow ID."""
    client = await tclient()
    workflow_id = f"doc-processor-{uuid.uuid4().hex}"

    agent_input = AgentWorkflowInput[DocProcessorCtx](
        context=ctx, wid=WorkflowInfo(wid=workflow_id, name=DocumentProcessorWorkflow.__name__)
    )

    queue = get_workflow_queue()
    await client.start_workflow(
        DocumentProcessorWorkflow.run,
        {"agent_input": agent_input.model_dump(mode="json")},
        id=workflow_id,
        task_queue=queue,
    )
    return {"workflow_id": workflow_id}

@router.get("/doc-processor/{workflow_id}")
async def doc_processor_status(workflow_id: str) -> dict:
    """Polls for the status and results of a DocumentProcessorWorkflow execution."""
    client: Client = await tclient()
    try:
        handle = client.get_workflow_handle(workflow_id)
        # The 'get_progress' query is provided by our BaseWorkflow
        progress = await handle.query("get_progress")
        if isinstance(progress, BaseModel):
            return progress.model_dump(mode="json")
        return progress
    except Exception as e:
        raise HTTPException(status_code=404, detail="Workflow not found or failed to query.") from e
```

### Step 3: Register the New Router

Finally, add your new router to the server in `antgent/server/server.py`.

```python
# antgent/server/server.py
from typing import ClassVar
from ant31box.server.server import Server

class AntgentServer(Server):
    _routers: ClassVar[set[str]] = {
        # ... other routers
        "antgent.server.api.job_info:router",
        "antgent.server.api.workflows.doc_processor:router",
    }
    # ...
```

You have now created a complete, executable, and API-accessible workflow that orchestrates an agent!
