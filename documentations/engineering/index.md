# Engineering Documentation Guides

This page provides links to detailed guides for common development tasks and architectural patterns within the antgent project. These are designed to help new engineers get up to speed quickly.

### Core Development Tasks

-   [**Testing Strategy**](testing-strategy.md): How to write effective unit and integration tests for agents and workflows using `pytest`.
-   [**Configuration Management**](configuration-management.md): How to manage configuration for the application, agents, and clients using Pydantic schemas, YAML files, and environment variables.
-   [**Debugging and Tracing**](debugging-and-tracing.md): How to debug issues using structured logging and distributed tracing with Logfire.
-   [**Using the Summarization System**](using-summarization-system.md): Comprehensive guide to the built-in text summarization capabilities, including multi-type summaries and iterative refinement.

### Extending the System

-   [**Adding a New Agent**](adding-a-new-agent.md): Step-by-step guide to creating custom agents.
-   [**Adding a New Workflow**](adding-a-workflow.md): How to orchestrate agents into complex, multi-step workflows.
-   [**Adding Agent Tools (Function Calling)**](adding-agent-tools.md): The pattern for creating and using tools that agents can call.
-   [**Integrating with External Services**](integrating-external-services.md): The standard pattern for adding new clients for external APIs.
-   [**Managing Data Models (Pydantic)**](managing-data-models.md): Best practices for creating and maintaining Pydantic models.

### Advanced & Operational Topics

-   [**Advanced Temporal Concepts**](advanced-temporal-concepts.md): A deeper dive into features like `RetryPolicy`, activity heartbeating, and using `tctl`.
-   [**Generating Reports (PDF/DOCX)**](generating-reports.md): How to create and integrate file-based reports into workflows.
-   [**Dependencies and Licenses**](dependencies-and-licenses.md): How to manage project dependencies and their licenses.
-   [**CI/CD and Deployment**](cicd-and-deployment.md): An overview of how the application is built, tested, and deployed.
