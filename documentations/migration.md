# Migration Guide

This guide outlines breaking changes introduced in new versions and provides instructions on how to update your code and configuration.

## Migrating to Version 0.9.0

Version 0.9.0 introduces clearer naming conventions to reduce confusion between workflow-level and agent-level concerns.

### Renamed: `AgentWorkflowInput` → `AgentInput`

The `AgentWorkflowInput` class has been renamed to `AgentInput` to better reflect its purpose. This class represents the input data for agents (containing `context` and `llm_input`), not workflow-level input.

### Renamed: `BaseWorkflowInput` → `WorkflowInput`

The `BaseWorkflowInput` class has been renamed to `WorkflowInput` for consistency and clarity. The "Base" prefix implied an abstract base class, but this is actually the concrete input model used directly by workflows.

**What Changed (AgentInput):**
- `AgentWorkflowInput[TInput]` is now `AgentInput[TInput]`
- The old name was misleading because this model is **not** the input for workflows—that's `WorkflowInput`
- This is purely a naming change; the functionality remains the same

**What Changed (WorkflowInput):**
- `BaseWorkflowInput[TInput]` is now `WorkflowInput[TInput]`
- Removes the misleading "Base" prefix which typically implies an abstract base class
- This is purely a naming change; the functionality remains the same

**Migration Steps:**

1. **Update your imports:**
```python
# Before
from antgent.models.agent import AgentWorkflowInput
from antgent.workflows.base import BaseWorkflowInput

# After
from antgent.models.agent import AgentInput
from antgent.workflows.base import WorkflowInput
```

2. **Update type annotations:**
```python
# Before (AgentInput)
agent_input: AgentWorkflowInput[MyContext] = AgentWorkflowInput(
    context=MyContext(...),
    llm_input=""
)

# After (AgentInput)
agent_input: AgentInput[MyContext] = AgentInput(
    context=MyContext(...),
    llm_input=""
)

# Before (WorkflowInput)
workflow_input: BaseWorkflowInput[MyContext] = BaseWorkflowInput(
    agent_input=agent_input,
    agent_config=config
)

# After (WorkflowInput)
workflow_input: WorkflowInput[MyContext] = WorkflowInput(
    agent_input=agent_input,
    agent_config=config
)
```

**Backwards Compatibility:**
- A backwards-compatible alias `AgentWorkflowInput = AgentInput` has been added
- A backwards-compatible alias `BaseWorkflowInput = WorkflowInput` has been added with a deprecation warning
- Existing code will continue to work, but you'll see deprecation warnings when using the old names
- We recommend updating to the new names for clarity and to avoid future issues

## Migrating to Version 0.8.0

Version 0.8.0 introduces dynamic agent configuration as an optional enhancement. **No breaking changes** - your existing code will continue to work without modifications.

### New Feature: Dynamic Agent Configuration

You can now override agent configurations at runtime when starting a workflow. This is entirely optional and backwards compatible.

#### Basic Usage

**Example: Override the model for all agents in a workflow**
```python
from antgent.workflows.base import WorkflowInput
from antgent.models.agent import AgentInput, DynamicAgentConfig

# Your workflow context
context = TextSummarizerWorkflowContext(content="...", to_language="en")
agent_input = AgentInput(context=context)

# Create dynamic configuration to use GPT-4o for all agents
dynamic_config = DynamicAgentConfig(model="gpt-4o")

# Pass it to the workflow
workflow_input = WorkflowInput(
    agent_input=agent_input,
    agent_config=dynamic_config
)
```

**Example: Configure specific agents**
```python
from antgent.models.agent import ModelInfo

# Override configuration for specific agents only
dynamic_config = DynamicAgentConfig(
    agents={
        "SummaryAgent": ModelInfo(model="claude-3-opus", client="litellm"),
        "GradeAgent": ModelInfo(model="gpt-4o", client="openai"),
    }
)

workflow_input = WorkflowInput(
    agent_input=agent_input,
    agent_config=dynamic_config
)
```

**Example: Add custom aliases for a workflow run**
```python
# Define temporary aliases that only apply to this workflow execution
dynamic_config = DynamicAgentConfig(
    aliases={
        "fast-model": "groq/llama-3-8b",
        "smart-model": "anthropic/claude-3-opus",
    },
    model="fast-model"  # Use the alias as the global default
)
```

#### API Integration

The API endpoints now accept the `agent_config` field in the request body:

```json
{
  "agent_input": {
    "context": {
      "content": "Your text here...",
      "to_language": "en"
    }
  },
  "agent_config": {
    "model": "gpt-4o",
    "aliases": {
      "fast": "gpt-3.5-turbo"
    },
    "agents": {
      "SummaryAgent": {
        "model": "claude-3-opus",
        "client": "litellm"
      }
    }
  }
}
```

#### Configuration Precedence

When using dynamic configuration, the following precedence applies (highest to lowest):

1. **Per-agent configuration**: `agent_config.agents["AgentName"]`
2. **Global model override**: `agent_config.model`
3. **Default configuration**: From `config.yaml` or agent defaults

This ensures that specific overrides always take precedence over general ones.

## Migrating to Version 0.6.0

Version 0.6.0 introduces significant improvements to the configuration and workflow invocation systems. Please review the following breaking changes to update your integration.

### 1. API Payload for Starting Workflows

The structure of the JSON payload for API endpoints that start a workflow (e.g., `POST /api/workflows/summarizer`) has changed. The `agent_input` is now nested inside a root object.

**Old Payload Structure:**
```json
{
  "agent_input": {
    "context": {
      "content": "Some text to summarize...",
      "to_language": "en"
    },
    // ... other agent_input fields
  }
}
```

**New Payload Structure:**
The `agent_input` is now passed directly as the top-level object.

```json
{
  "context": {
    "content": "Some text to summarize...",
    "to_language": "en"
  },
  // ... other context fields
}
```
*Note: The API endpoint for re-triggering a workflow (`/summarizer/retrigger`) now also expects the new payload structure, where `context` and `wid` are top-level keys.*


### 2. Configuration File Changes (`config.yaml`)

The structure of the `temporalio` configuration section has been updated to align with `temporalloop` version 0.2.

**Old Configuration (`temporalio` section):**
The `temporalloop.config_loader.TemporalConfigSchema` was used, which had a slightly different structure.

**New Configuration (`temporalio` section):**
The schema now directly uses `temporalloop.config.TemporalSettings`. The main changes are:
-   `metric_bind_address` is no longer a field on workers.
-   The structure is flatter and cleaner.

Please refer to the default configuration for the updated structure by running: `antgent default-config`

### 3. Temporal Client Initialization

The internal Temporal client (`tclient`) is now a singleton managed within `antgent.temporal.client`. This change should be transparent unless you were directly instantiating the client. The recommendation is to always use the `antgent.temporal.client.tclient()` async function to get a client instance.
