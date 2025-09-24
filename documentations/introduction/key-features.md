# Key Features

antgent is packed with features designed to make building and managing AI agent workflows as seamless as possible.

-   **Asynchronous & Fault-Tolerant Workflows**: Built on [Temporal.io](https://temporal.io/), workflows are resilient to failures and can reliably run for seconds, days, or even months. The state of your long-running executions is automatically preserved.

-   **Modular Agent Design**: Develop agents as independent, single-purpose components. This modularity allows for easy testing in isolation and reusability across different workflows, promoting a clean and maintainable codebase.

-   **Structured Data with Pydantic**: antgent enforces data integrity and clarity using Pydantic models. This eliminates a whole class of runtime data errors by ensuring all inputs and outputs for agents and workflows are validated and type-safe.

-   **Ready-to-use API Server**: With [FastAPI](https://fastapi.tiangolo.com/) integration, any workflow can be exposed as a RESTful API endpoint with minimal configuration. It supports both synchronous (blocking) and asynchronous (non-blocking) execution patterns out-of-the-box.

-   **Built-in Observability**: Workflows and agents are automatically instrumented for logging and tracing. This gives you deep visibility into your system's execution, making it easier to debug issues and monitor performance.

-   **Flexible Configuration**: A unified configuration system allows you to manage settings for your application, agents, third-party services, and infrastructure all in one place. It supports environment variables for easy deployment across different environments (development, staging, production).
