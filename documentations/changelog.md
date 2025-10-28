# Changelog

This document records the major changes for each version of the `antgent` framework.

## Version 0.12.0

This release introduces a comprehensive redesign of the summarization system with support for multiple summary types, iterative refinement, and enhanced API patterns.

### ✨ Features & Improvements

-   **Multi-Type Summarization**: New `SummaryType` enum supports distinct summary types:
    -   `MACHINE`: Comprehensive summaries optimized for LLM processing
    -   `PRETTY`: Concise summaries optimized for human reading
-   **Iterative Refinement**: Summaries can now be improved through multiple iterations with automatic quality grading via judge agents
-   **Split Workflow Architecture**: The monolithic summarizer workflow has been split into:
    -   `TextSummarizerOneTypeWorkflow`: Generates a single summary type
    -   `TextSummarizerAllWorkflow`: Generates all summary types in parallel
-   **Enhanced API Endpoints**: New endpoints support both synchronous (wait for result) and asynchronous (returns workflow_id) patterns
-   **Generic Status Endpoint**: New `/api/workflows/status/{workflow_id}` endpoint works for any workflow type
-   **Model Separation**: Clear distinction between internal workflow models and external API responses

### 💥 Breaking Changes

-   **Workflow Renames**: `TextSummarizerWorkflow` split into `TextSummarizerOneTypeWorkflow` and `TextSummarizerAllWorkflow`
-   **Model Updates**: `SummaryResult` replaced with `InternalSummaryResult`, `InternalSummariesAllResult`, and `SummariesResult`
-   **Activity Renames**: `run_summarizer_activity` renamed to `run_summarizer_one_type_activity`

### 🔄 Migration Notes

See the [What's New: v0.12.0](whatsnew/2025-10-28-updates.md) guide for detailed migration instructions and integration patterns.

## Version 0.9.0

This release focuses on improved clarity and consistency in the codebase, with significant renames to reduce confusion about workflow vs. agent inputs.

### 💥 Breaking Changes

-   **Renamed `AgentWorkflowInput` to `AgentInput`**: This class has been renamed to better reflect its purpose. It represents the input data for agents (containing `context` and `llm_input`), not workflow-level input. A backwards-compatible alias has been added, but we recommend updating to the new name.
    -   **Before**: `AgentWorkflowInput[TContext]`
    -   **After**: `AgentInput[TContext]`
    -   See the [Migration Guide](migration.md#migrating-to-version-090) for detailed instructions.

-   **Renamed `BaseWorkflowInput` to `WorkflowInput`**: This class has been renamed for consistency and clarity. The "Base" prefix implied an abstract base class, but this is actually the concrete input model used directly by workflows. A backwards-compatible alias with a deprecation warning has been added.
    -   **Before**: `BaseWorkflowInput[TContext]`
    -   **After**: `WorkflowInput[TContext]`
    -   **Deprecation**: Using `BaseWorkflowInput` will trigger a deprecation warning. It will be removed in version 1.0.0.
    -   See the [Migration Guide](migration.md#migrating-to-version-090) for detailed instructions.

### 📚 Documentation

-   Updated all documentation and examples to use the new `AgentInput` and `WorkflowInput` naming
-   Clarified the distinction between agent-level inputs (`AgentInput`) and workflow-level inputs (`WorkflowInput`)
-   Added comprehensive migration guide with examples for both renames

## Version 0.8.0

This release introduces powerful runtime configuration capabilities for workflows, allowing dynamic model selection and agent configuration without modifying code or static configuration files.

### ✨ Features & Improvements

-   **Dynamic Agent Configuration**: Workflows can now accept runtime configuration overrides through the new `DynamicAgentConfig` model. This allows you to:
    -   Set a global model override for all agents in a workflow execution
    -   Define custom model aliases for a specific workflow run
    -   Configure individual agents with specific models, clients, and settings
    -   Create new agent configurations on-the-fly
-   **Flexible Model Selection**: The `BaseWorkflowInput` now includes an optional `agent_config` field that accepts `DynamicAgentConfig`, enabling per-execution customization of:
    -   LLM models (e.g., switching from GPT-4 to Claude for a specific run)
    -   API clients and endpoints
    -   Token limits and other model settings
-   **Configuration Precedence**: Clear precedence rules ensure predictable behavior:
    1. Per-agent overrides in `agent_config.agents[name]` (highest priority)
    2. Global model override in `agent_config.model`
    3. Default configuration from `config.yaml` (lowest priority)
-   **Comprehensive Test Coverage**: Added extensive tests for all dynamic configuration scenarios, including edge cases, circular dependency detection, and complex override combinations.

### 📚 Documentation

-   All engineering guides and examples have been updated to reflect best practices for dynamic configuration
-   Added detailed test examples demonstrating various configuration patterns

### 🔧 Technical Details

-   The `_apply_dynamic_config` method in `BaseWorkflow` handles the merging of runtime and default configurations
-   Alias resolution is integrated with the configuration system for seamless model name translation
-   All configuration changes are isolated to individual workflow executions, ensuring no cross-contamination

## Version 0.6.0

This release focuses on improving the developer experience by aligning more closely with the underlying `temporalloop` library, enhancing configuration, and introducing a more robust API for starting workflows.

### ✨ Features & Improvements

-   **Workflow Input Standardization**: The API endpoints for starting workflows (e.g., `/summarizer`) now accept a standardized `BaseWorkflowInput` object. This provides better type safety and consistency when initiating workflows.
-   **CLI Enhancements for Temporal Workers**: The `antgent worker looper` command now directly exposes all options from the underlying `temporalloop` worker, such as `--queue`, `--workflow`, and `--activity`. This makes it much easier to run and debug specific workers from the command line without needing a configuration file.
-   **Simplified Configuration**: The internal configuration handling for Temporal workers has been streamlined. There is now a convenient `config().workers` property to access worker configurations.
-   **Documentation Updates**:
    -   Added a new Migration Guide to help developers upgrade between versions.
    -   Added this Changelog to keep track of new features and changes.
    -   Updated engineering guides to reflect the latest code patterns.

### 💥 Breaking Changes

-   The API payload for starting workflows has changed. Please see the [Migration Guide](migration.md) for details on how to update your API calls.
-   The structure of the `temporalio` section in `config.yaml` has been updated to align with `temporalloop` v0.2. Please refer to the [Migration Guide](migration.md) for configuration changes.
