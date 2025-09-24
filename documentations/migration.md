# Migration Guide

This guide outlines breaking changes introduced in new versions and provides instructions on how to update your code and configuration.

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
