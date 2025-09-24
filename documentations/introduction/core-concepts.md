# Core Concepts

Understanding these core concepts is key to effectively using the antgent framework.

### Agents

An **Agent** is a specialized Python class that encapsulates the logic for performing a single, well-defined task. Think of an agent as an expert with a specific skill. For example, you might have:

-   A `ClassifierAgent` that categorizes documents.
-   A `SummarizerAgent` that condenses long texts.
-   A `DataFetchingAgent` that calls an external API to retrieve information.

Agents are designed to be modular and reusable. You can develop and test them independently before integrating them into larger, more complex systems.

### Workflows

A **Workflow** is the orchestration logic that defines how one or more agents collaborate to achieve a complex goal. Workflows are defined as Python code and are executed by a Temporal.io worker.

Key characteristics of antgent workflows:

-   **Durability**: They are fault-tolerant and can recover from process failures.
-   **Statefulness**: Temporal automatically persists the state of a workflow, so it can resume exactly where it left off, even after long delays.
-   **Scalability**: Workflows can be distributed across multiple workers to handle high loads.

A workflow might define a sequence of agent calls, parallel executions, or conditional logic based on agent outputs.

### Models

**Models** are Pydantic data classes that define the structure of data within the antgent framework. They serve as contracts for inputs and outputs of agents, workflows, and API endpoints.

Using Pydantic models provides:

-   **Data Validation**: Automatic validation of incoming data to prevent errors.
-   **Type Safety**: Clear, explicit data types that improve code readability and are leveraged by IDEs for better autocompletion and error checking.
-   **Self-Documentation**: The models themselves serve as a form of documentation for what data is expected.

### API Server

antgent includes a built-in **API Server** powered by FastAPI. This server exposes your workflows as RESTful API endpoints, making it easy to integrate your agent systems with other applications, such as web frontends or other microservices.

The server is designed to handle both:
- **Synchronous requests**: The API call waits for the workflow to complete and returns the final result.
- **Asynchronous requests**: The API call immediately returns a job ID, which can be used later to poll for the status and retrieve the result of the workflow. This is ideal for long-running tasks.
