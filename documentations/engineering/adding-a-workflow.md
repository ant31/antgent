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

Let's create a hypothetical `DocumentProcessorWorkflow` that receives a document, summarizes it using the summarization agents, and returns the result. This example demonstrates the patterns introduced in v0.12.0.

### Step 1: Define Input and Output Models

First, define the Pydantic models for your workflow's context (input) and final result (output). This is typically done in a `models.py` file within your workflow's directory (e.g., `antgent/workflows/doc_processor/models.py`).

```python
# antgent/workflows/doc_processor/models.py
from antgent.agents.summarizer.models import SummaryInput, SummaryOutput, SummaryType
from pydantic import Field

class DocProcessorCtx(SummaryInput):
    """
    Context for document processing workflow.
    Inherits from SummaryInput to use summarization features.
    """
    # You can add extra fields specific to your workflow
    priority: int = Field(default=1, description="Processing priority")
    
    # Configure summarization behavior
    summary_type: SummaryType = Field(
        default=SummaryType.MACHINE, 
        description="Type of summary to generate"
    )
    iterations: int = Field(default=2, description="Number of refinement iterations")

class DocProcessorResult(SummaryOutput):
    """
    Result from document processing workflow.
    Inherits from SummaryOutput which provides structured summary data.
    """
    # Add any extra output fields
    processing_time_seconds: float | None = Field(default=None)
```

### Step 2: Create Activities

Now, create the activities that will execute your agents. In v0.12.0+, we use the reusable summarization logic from `antgent.agents.summarizer.logic`.

**Best Practice:** Activities should be thin wrappers around agent logic. For summarization workflows, leverage the existing `summarize_one_type` function.

```python
# antgent/workflows/doc_processor/workflow.py
import logging
from temporalio import activity, exceptions
from antgent.agents.summarizer.logic import summarize_one_type
from antgent.agents.summarizer.models import InternalSummaryResult
from .models import DocProcessorCtx

logger = logging.getLogger(__name__)

@activity.defn
async def process_document_activity(ctx: DocProcessorCtx) -> InternalSummaryResult:
    """
    Activity to process and summarize a document.
    
    Uses the centralized summarization logic which handles:
    - Agent selection based on summary_type
    - Iterative refinement with grading
    - Best summary selection
    """
    logger.info(
        "Processing document with type=%s, iterations=%d",
        ctx.summary_type,
        ctx.iterations
    )
    
    # Use the shared summarization logic
    result = await summarize_one_type(ctx)
    
    if not result or not result.summary:
        raise exceptions.ApplicationError(
            "Failed to generate summary", 
            non_retryable=True
        )
    
    return result
```

### Step 3: Implement the Workflow Class

Now, assemble the activities in your workflow's `run` method. Our `BaseWorkflow` provides helpers for tracking progress.

-   `self._init_run(data)`: Initializes the workflow run and progress tracking
-   `self._update_status(...)`: Updates the status of a step in the workflow's execution graph (visible via API)
-   `workflow.execute_activity()`: Executes an activity with timeout and retry settings

```python
# antgent/workflows/doc_processor/workflow.py
import time
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from antgent.models.agent import AgentWorkflowOutput
from antgent.workflows.base import BaseWorkflow, WorkflowInput
from antgent.models.visibility import WorkflowStepStatus
from .models import DocProcessorCtx, DocProcessorResult

@workflow.defn
class DocumentProcessorWorkflow(BaseWorkflow[DocProcessorCtx, DocProcessorResult]):
    """
    Workflow for processing documents with configurable summarization.
    
    This workflow demonstrates:
    - Using the new summarization logic
    - Progress tracking
    - Proper activity configuration
    """
    
    def __init__(self) -> None:
        super().__init__()

    @workflow.run
    async def run(
        self, 
        data: WorkflowInput[DocProcessorCtx]
    ) -> AgentWorkflowOutput[DocProcessorResult]:
        # Initialize workflow run tracking
        self._init_run(data)
        ctx = data.agent_input.context
        
        self._update_status("Workflow Start", WorkflowStepStatus.COMPLETED)
        
        # Track start time for metrics
        start_time = workflow.now()
        
        # Configure activity execution
        self._update_status("Document Processing", WorkflowStepStatus.RUNNING)
        retry_policy = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=5),
            maximum_interval=timedelta(minutes=1),
            backoff_coefficient=2.0,
        )
        
        # Execute the summarization activity
        internal_result = await workflow.execute_activity(
            process_document_activity,
            ctx,
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )
        
        self._update_status("Document Processing", WorkflowStepStatus.COMPLETED)
        
        # Extract the final summary and add processing time
        processing_time = (workflow.now() - start_time).total_seconds()
        final_result = DocProcessorResult(
            **internal_result.summary.model_dump(),
            processing_time_seconds=processing_time
        )
        
        self.result = AgentWorkflowOutput(
            result=final_result, 
            workflow_info=data.wid
        )
        self._update_status("Workflow End", WorkflowStepStatus.COMPLETED)
        return self.result
```

**Key Points:**

- Use `WorkflowInput[TContext]` (not the deprecated `BaseWorkflowInput`)
- Configure appropriate timeouts for your activities
- Use retry policies for resilience
- Track progress with `_update_status` for API visibility
- Extract clean output models from internal results

### Step 4: Register the Workflow and Activities

For Temporal to recognize your new workflow and activities, register them in your configuration file (e.g., `localconfig.yaml`).

```yaml
# localconfig.yaml
temporalio:
  workers:
    - name: "antgent-workflow"
      queue: "antgent-queue"
      workflows:
        # Existing workflows
        - "antgent.workflows.summarizer.text:TextSummarizerOneTypeWorkflow"
        - "antgent.workflows.summarizer.text:TextSummarizerAllWorkflow"
        # Your new workflow
        - "antgent.workflows.doc_processor.workflow:DocumentProcessorWorkflow"

    - name: "antgent-activities"
      queue: "antgent-queue-activity"
      activities:
        # Existing activities
        - "antgent.workflows.summarizer.text:run_summarizer_one_type_activity"
        # Your new activity
        - "antgent.workflows.doc_processor.workflow:process_document_activity"
```

**Note:** You can also define these in `antgent/config.py` as default values, but using `localconfig.yaml` is more flexible for different deployment environments.

## 3. Exposing the Workflow via API

To make your workflow accessible, you need to create API endpoints.

### Step 1: Create an API Router

Create a new file, for example, `antgent/server/api/workflows/doc_processor.py`.

### Step 2: Implement the API Endpoints

Modern workflows should support both synchronous (wait for result) and asynchronous (returns workflow_id) patterns. Here's how to implement both:

```python
# antgent/server/api/workflows/doc_processor.py
import asyncio
import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from temporalio.client import Client

from antgent.models.agent import AgentWorkflowOutput
from antgent.models.visibility import WorkflowInfo
from antgent.server.api.status import get_workflow_status
from antgent.temporal.client import tclient
from antgent.temporal.queue_manager import get_workflow_queue
from antgent.workflows.base import WorkflowInput
from antgent.workflows.doc_processor.workflow import DocumentProcessorWorkflow
from antgent.workflows.doc_processor.models import DocProcessorCtx, DocProcessorResult

router = APIRouter(prefix="/api/workflows", tags=["DocProcessor"])

# Synchronous endpoint - waits for result
@router.post("/doc-processor/sync", tags=["sync"])
async def process_document_sync(
    ctx: WorkflowInput[DocProcessorCtx],
    client: Annotated[Client, Depends(tclient)]
) -> AgentWorkflowOutput[DocProcessorResult]:
    """
    Executes document processing workflow and waits for the result.
    
    Use this endpoint when:
    - You need immediate results
    - The processing time is predictable (<5 min)
    - Your client can maintain a long HTTP connection
    """
    workflow_id = f"doc-processor-sync-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=DocumentProcessorWorkflow.__name__)
    queue = get_workflow_queue()
    
    handle = await client.start_workflow(
        DocumentProcessorWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    
    try:
        timeout_seconds = timedelta(minutes=10).total_seconds()
        result = await asyncio.wait_for(handle.result(), timeout=timeout_seconds)
        return result
    except TimeoutError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Workflow did not complete within timeout",
                "workflow_id": workflow_id,
                "timeout": timeout_seconds,
            }
        ) from exc

# Asynchronous endpoint - returns workflow_id immediately
@router.post("/doc-processor/run", tags=["async"])
async def run_document_processor(
    ctx: WorkflowInput[DocProcessorCtx],
    client: Annotated[Client, Depends(tclient)]
) -> dict[str, str]:
    """
    Starts a document processing workflow and returns the workflow ID.
    
    Use this endpoint when:
    - Processing may take a long time (>5 min)
    - You want to poll for status separately
    - Your system needs to handle many concurrent requests
    """
    workflow_id = f"doc-processor-{uuid.uuid4().hex}"
    ctx.wid = WorkflowInfo(wid=workflow_id, name=DocumentProcessorWorkflow.__name__)
    queue = get_workflow_queue()
    
    await client.start_workflow(
        DocumentProcessorWorkflow.run,
        ctx,
        id=workflow_id,
        task_queue=queue,
    )
    return {"workflow_id": workflow_id}

# Status endpoint - works with async pattern
@router.get("/doc-processor/{workflow_id}/status", tags=["async"])
async def doc_processor_status(
    workflow_id: str,
    client: Annotated[Client, Depends(tclient)]
) -> dict:
    """
    Polls for the status and results of a DocumentProcessorWorkflow execution.
    
    Returns progress information and final results when complete.
    """
    return await get_workflow_status(workflow_id, client)
```

**API Design Best Practices:**

1. **Sync endpoints** (`/sync`): Good for short-running workflows (<5 min)
2. **Async endpoints** (`/run` + `/status`): Better for long-running workflows
3. **Use dependency injection**: `Annotated[Client, Depends(tclient)]` ensures proper client lifecycle
4. **Consistent naming**: Use clear prefixes like `/sync`, `/run`, `/status`
5. **Proper timeouts**: Configure based on expected workflow duration

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
