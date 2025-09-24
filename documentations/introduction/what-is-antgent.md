# What is antgent?

antgent is a powerful Python framework designed for creating, orchestrating, and deploying sophisticated multi-agent AI systems. It provides a robust foundation for building applications that leverage the power of multiple AI agents collaborating to solve complex problems.

At its core, antgent is built to handle complex, long-running, and fault-tolerant tasks. It achieves this by leveraging [Temporal.io](https://temporal.io/) for workflow orchestration, ensuring that your multi-step processes are reliable and scalable. Whether you are building systems for legal document analysis, financial report summarization, or intelligent data pipelines, antgent provides the tools to manage the complexity.

The framework emphasizes a modular and structured development approach. Key components include:

-   **Modular Agents**: Agents are designed as independent, reusable components, each with a specific skill or purpose.
-   **Declarative Workflows**: Workflows are defined as Python code, making it easy to express the logic of agent collaboration.
-   **Type Safety**: With extensive use of [Pydantic](https://docs.pydantic.dev/), antgent ensures that data flowing through your system is validated and consistent.
-   **API-First Design**: Built-in integration with [FastAPI](https://fastapi.tiangolo.com/) allows you to quickly expose your agent workflows as robust RESTful API endpoints.

antgent is ideal for developers and teams looking to move beyond simple, single-prompt AI applications and build sophisticated systems that can reason, plan, and execute complex tasks reliably.
