# Adding Agent Tools (Function Calling)

Agents can be given "tools" that they can decide to call to get more information or perform actions. This is often referred to as "function calling." In our framework, this is achieved using the `@function_tool` decorator.

This guide explains how to create and use a new tool for an agent.

## Core Concepts

-   **`@function_tool`**: A decorator that exposes a Python function to an agent as a callable tool. The agent's underlying LLM can then decide to call this function during its reasoning process.
-   **`RunContextWrapper`**: A wrapper object that provides the tool function with access to the agent's current context (`ctx.context`). This allows the tool to use data from the agent's input to perform its task.

## Step 1: Create the Tool Function

A tool is an `async` Python function that performs a specific, well-defined action, such as fetching data from an external API or a database.

The function must be decorated with `@function_tool` and should accept one argument: `ctx: RunContextWrapper[YourAgentInputModel]`.

**Example: A tool to get the current date**
Here is a simple tool that returns the current date.

```python
# In a functions.py file for your agent
from datetime import date
from agents import RunContextWrapper, function_tool
from pydantic import BaseModel

class MyAgentInput(BaseModel):
    # Define your agent's input model
    pass

@function_tool
async def get_current_date_tool(ctx: RunContextWrapper[MyAgentInput]) -> str:
    """Gets the current date as a string."""
    _ = ctx # The context is available if needed
    return date.today().isoformat()
```

**Key Points:**
-   The function's docstring is crucial! The LLM uses the docstring to understand what the tool does and when to call it. It should be a clear, concise description of the tool's purpose.
-   The function must return a `str`. This string is what the LLM will see as the result of the tool call. It's often best to return data in a structured format like JSON or a clear natural language summary.

## Step 2: Make the Tool Available to the Agent

To allow an agent to use a tool, you need to configure the agent to be aware of it. This is typically done by setting the `model_settings` in the agent's `default_config`.

The `tool_choice` setting controls how the agent uses tools:
-   `tool_choice="auto"`: The LLM decides whether to call a function or respond directly.
-   `tool_choice="none"`: The LLM is forced to respond directly and cannot call any functions.
-   `tool_choice={"type": "function", "function": {"name": "my_tool_name"}}`: The LLM is forced to call a specific function.

You also need to provide the list of available tools.

**Example: Configuring an agent to use tools**
```python
# In an agent definition file (e.g., antgent/agents/my_agent/agent.py)
from agents import ModelSettings
from antgent.agents.base import AgentConfig
# Import your tool function
from .functions import get_current_date_tool

# ...
    default_config = AgentConfig(
        name="MyToolAgent",
        client="litellm",
        model="openai/gpt-4o",
        # Configure model settings for function calling
        model_settings=ModelSettings(
            tool_choice="auto",
            tools=[get_current_date_tool]
        )
    )
    # ... rest of the agent implementation
```

Once configured, the agent's underlying LLM will be aware of the tools. The agent's base `workflow` method handles the logic of executing the tool call and sending the result back to the LLM for a final answer.
