# Changelog

This document records the major changes for each version of the `antgent` framework.

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
