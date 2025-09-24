# Debugging and Tracing

Effective debugging and observability are critical for understanding and maintaining complex agent-based systems. This project uses a combination of structured logging and distributed tracing with [Logfire](https://logfire.pydantic.dev/) to provide deep insights into the execution of agents and workflows.

## Structured Logging

The project uses Python's standard `logging` module, configured to output structured logs (usually in JSON format in production). This makes logs easy to parse, search, and analyze in log management systems.

**Getting a Logger:**
Always use `logging.getLogger(__name__)` at the module level to get a logger instance.

```python
import logging

logger = logging.getLogger(__name__)

def my_function(data):
    logger.info("Processing data for item %s", data.id)
    try:
        # ... logic
    except Exception as e:
        logger.error("Failed to process item %s: %s", data.id, e, exc_info=True)
```

**Best Practices:**
-   Use log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) appropriately.
-   Use string formatting with arguments (`logger.info("User %s logged in", user.name)`) instead of f-strings (`logger.info(f"User {user.name} logged in")`). This is more performant as the string formatting is only done if the log message is actually emitted.
-   Include `exc_info=True` when logging exceptions to capture the full stack trace.

## Distributed Tracing with Logfire

We use Logfire for distributed tracing, which allows us to visualize the entire lifecycle of a request as it passes through different agents, workflows, and external services.

### Automatic Instrumentation

Logfire is configured to automatically instrument key libraries like `openai`, providing traces for LLM calls out-of-the-box. This is configured in `antgent/clients.py`.

### Custom Spans

To get more granular visibility into your own code, you can create custom spans. A span represents a single unit of work (e.g., a function call, a block of code).

The easiest way to create a span is with the `@custom_span` decorator or `with custom_span()` context manager from the `agents` library.

**Example: Using a context manager in an agent's workflow**
```python
# In an agent's method
from agents import custom_span
from antgent.agents.base import BaseAgent

class MyAgent(BaseAgent[...]):
    # ...

    async def workflow(self, llm_input, context):
        with custom_span("My Agent Workflow"):
            # The agent's logic is now wrapped in a span
            return await super().workflow(llm_input, context)
```
This will create a span named "My Agent Workflow" in your trace, timing the execution of the agent's main workflow method.

**Example: Adding attributes to a span**
You can add key-value attributes to spans to record important context about the operation.

```python
# In a workflow or activity
from agents import custom_span

with custom_span("Processing item", attributes={"item_id": 123, "user": "test"}):
    # ... logic for processing the item
```

### Tracing in Temporal Workflows

Our `BaseWorkflow` class and activity runners are integrated with the tracing system. When a workflow runs, it creates a root trace, and each activity and significant step within the workflow becomes a child span. This provides an end-to-end view of the workflow's execution, including time spent in each activity.

By combining structured logs with detailed traces, you can effectively diagnose issues, identify performance bottlenecks, and gain a comprehensive understanding of how your agent system is behaving.
