# Advanced Temporal Concepts

Our workflows are built on Temporal.io, which provides several powerful features for building reliable, long-running applications. This guide covers some of the advanced Temporal concepts we use in this project.

## Retry Policies

Activities in Temporal can automatically be retried if they fail. This is configured using a `RetryPolicy`. This is crucial for making our workflows resilient to transient failures, such as temporary network issues or rate limiting from external APIs.

A `RetryPolicy` can be configured with:
-   `maximum_attempts`: The maximum number of times to retry the activity.
-   `initial_interval`: The delay before the first retry.
-   `maximum_interval`: The maximum delay between retries.
-   `backoff_coefficient`: The multiplier for the retry delay (e.g., `2.0` for exponential backoff).
-   `non_retryable_error_types`: A list of exception types that should *not* trigger a retry.

**Example: An activity with a retry policy**
```python
# antgent/workflows/summarizer.py
from temporalio.common import RetryPolicy
from datetime import timedelta
from temporalio import workflow

# ... inside a workflow's run method
result = await workflow.execute_activity(
    run_summarizer_activity,
    ctx,
    start_to_close_timeout=timedelta(minutes=5),
    heartbeat_timeout=timedelta(minutes=1),
    retry_policy=RetryPolicy(maximum_attempts=3),
)
```

## Activity Heartbeating

For long-running activities (like those involving slow LLM calls or processing large files), it's important for the activity to periodically report its progress back to the Temporal server. This is called **heartbeating**.

If the Temporal server doesn't receive a heartbeat within the configured `heartbeat_timeout`, it will consider the activity to have failed and will schedule a retry. This prevents activities from getting stuck indefinitely.

We use a helper context manager `heartbeat_every` from `antgent.workflows.base` to handle this automatically.

**Example: An activity with heartbeating**
```python
# antgent/workflows/base.py
from antgent.workflows.base import heartbeat_every
from temporalio import activity

@activity.defn
async def demo_activity_with_heartbeat() -> int:
    """Activity to demonstrate heartbeating."""
    async with heartbeat_every(): # Sends a heartbeat every 30 seconds by default
        # ... long running logic ...
        return 1
```

## Inspecting Workflows with `tctl`

`tctl` is the command-line interface for Temporal. It's an invaluable tool for debugging and inspecting workflows.

**Prerequisites:** You need to have `tctl` installed and configured to connect to your Temporal cluster.

**Common Commands:**

-   **List running workflows:**
    ```bash
    tctl workflow list --query "ExecutionStatus='Running'"
    ```

-   **Show the history of a workflow:**
    This shows every event that has occurred in the workflow's execution, which is extremely useful for debugging.
    ```bash
    tctl workflow show --workflow-id "your-workflow-id"
    ```

-   **Query a running workflow:**
    If a workflow has a query handler defined (like our `get_progress` or `get_status` queries), you can call it.
    ```bash
    tctl workflow query --workflow-id "your-workflow-id" --query-type "get_progress"
    ```

-   **Terminate a workflow:**
    ```bash
    tctl workflow terminate --workflow-id "your-workflow-id" --reason "Debugging"
    ```

Mastering these concepts will help you build and maintain workflows that are not only powerful but also robust and easy to manage.
