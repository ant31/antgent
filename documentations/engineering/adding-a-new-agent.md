# How to Add a New Agent

Agents are the fundamental building blocks of the antgent framework. Each agent is a specialized Python class designed to perform a single, well-defined task by interacting with a Large Language Model (LLM). This guide explains the structure of an agent and how to create a new one.

## Core Concepts of an Agent

An agent in antgent is a class that inherits from `antgent.agents.base.BaseAgent`. It has a few key components:

-   **Input and Output Models**: Pydantic models define the structure of the data an agent works with.
    -   `TCtx`: The **Context Model**, defining the input data the agent needs to perform its task.
    -   `TOutput`: The **Output Model**, defining the structured data the agent is expected to return.
-   **Configuration**:
    -   `agent_config`: An `AgentFrozenConfig` that defines immutable properties, like the output class (`output_cls`).
    -   `default_config`: An `AgentConfig` that defines default settings like the agent's name, description, and the LLM model to use (e.g., `gemini/gemini-pro`).
-   **Core Methods**:
    -   `prompt()`: Returns the system prompt or instructions for the LLM.
    -   `prep_input()`: Prepares the final input to be sent to the LLM, typically by combining the prompt and the context data.
    -   `prep_response()`: (Optional) Post-processes the raw output from the LLM before it's validated against the output model.

## Step-by-Step Guide to Creating a New Agent

Let's create a simple `EchoAgent` that takes some text and returns it in a structured format.

### Step 1: Define the Directory Structure

It's best practice to organize each agent into its own directory within `antgent/agents/`.

```
antgent/
└── agents/
    └── echo_agent/
        ├── __init__.py
        ├── models.py
        └── agent.py
```

### Step 2: Define the Input and Output Models

In `antgent/agents/echo_agent/models.py`, define the Pydantic models for your agent's context and output.

```python
# antgent/agents/echo_agent/models.py
from pydantic import BaseModel, Field

class EchoAgentInput(BaseModel):
    """The context (input) for our Echo Agent."""
    message: str = Field(..., description="The message to be echoed.")
    repeat_count: int = Field(default=1, description="How many times to repeat the message.")

class EchoAgentOutput(BaseModel):
    """The structured output from our Echo Agent."""
    echoed_message: str = Field(..., description="The final echoed message.")
    source_message: str = Field(..., description="The original message received.")
```

### Step 3: Implement the Agent Class

In `antgent/agents/echo_agent/agent.py`, create the agent class.

```python
# antgent/agents/echo_agent/agent.py
import logging
from agents import TResponseInputItem
from antgent.agents.base import BaseAgent, PrepareRun, TLLMInput
from antgent.models.agent import AgentConfig, AgentFrozenConfig

from .models import EchoAgentInput, EchoAgentOutput

PROMPT_ECHO = """
You are a simple echo bot. Take the user's message and repeat it the specified number of times.
Combine the repeated messages into a single string.
"""

class EchoAgent(BaseAgent[EchoAgentInput, EchoAgentOutput]):
    # A unique identifier for the agent
    name_id = "EchoAgent"

    # Frozen config: defines the output model for validation
    agent_config = AgentFrozenConfig[EchoAgentOutput, EchoAgentOutput](output_cls=EchoAgentOutput, structured=True)

    # Default config: can be overridden in the main application config
    default_config = AgentConfig(
        name="EchoAgent",
        client="litellm",  # Use the default configured LLM client
        description="Echoes a message back in a structured format.",
        model="gemini/gemini-flash",  # A fast and cheap model is good for simple tasks
    )

    def prompt(self) -> str:
        """
        Returns the static system prompt for the LLM.
        """
        return PROMPT_ECHO

    async def prep_input(self, llm_input: TLLMInput, ctx: EchoAgentInput) -> PrepareRun[EchoAgentInput]:
        """
        Prepares the list of messages to be sent to the LLM.
        """
        # The llm_input is an empty list that we populate.
        # It comes from the base class `workflow` method.
        messages: list[TResponseInputItem] = []

        # Construct the user message with the data from our context object
        user_content = f"Please echo the following message {ctx.repeat_count} times: '{ctx.message}'"
        messages.append({"role": "user", "content": user_content})

        self.add_inputs(llm_input, messages)

        # PrepareRun is a container for the final inputs.
        # short_cut=False means the agent will proceed to call the LLM.
        return PrepareRun(llm_input=messages, context=ctx, short_cut=False)

```

### Step 4: Using Your New Agent

Your `EchoAgent` is now ready to be used within a workflow or an API endpoint. You can instantiate it and call its `workflow` method:

```python
# In a workflow or API endpoint
from antgent.agents.echo_agent.agent import EchoAgent
from antgent.agents.echo_agent.models import EchoAgentInput

# Instantiate the agent
echo_agent = EchoAgent()

# Create the input context
agent_context = EchoAgentInput(message="Hello, World!", repeat_count=3)

# Run the agent's workflow
result = await echo_agent.workflow("", context=agent_context)

if result:
    # result is an instance of EchoAgentOutput
    print(result.echoed_message)
    # Expected output might be: "Hello, World! Hello, World! Hello, World!"
```

This completes the process of adding a new, self-contained, and reusable agent to the antgent system.
