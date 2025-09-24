<div align="center">
  <h1>🐜 AntGent</h1>
  <p><strong>Build Fault-Tolerant, Multi-LLM Agentic Workflows with Temporal</strong></p>

  [![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
  [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
  [![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

**AntGent** is a powerful Python framework for building, orchestrating, and scaling complex AI-powered workflows. By combining the robustness of **Temporal** for durable execution with the flexibility of **LiteLLM** for multi-provider LLM access, AntGent empowers you to create sophisticated agentic systems that are resilient, observable, and easy to manage.

Whether you're building a multi-step document processing pipeline, a conversational AI that remembers context over days, or a complex data analysis agent, AntGent provides the foundational tools to do it right.

## ✨ Key Features

-   **⚙️ Durable & Stateful Workflows**: Powered by [Temporal](https://temporal.io/), your workflows are fully stateful and survive failures, ensuring long-running, complex tasks complete reliably without data loss.
-   **🧠 Modular Agent Architecture**: Build your systems from reusable, single-purpose AI agents. AntGent provides a `BaseAgent` class to make creating new agents a breeze.
-   **🌐 Multi-LLM Flexibility**: Integrated with [LiteLLM](https://litellm.ai/), you can seamlessly switch between dozens of LLM providers (OpenAI, Gemini, Anthropic, Cohere, local models, etc.) with just a configuration change.
-   **🚀 Ready-to-Use Components**: Get started quickly with built-in workflows and agents, such as a powerful, iterative text summarizer.
-   **⚡ High-Performance API**: A modern, asynchronous API server built with [FastAPI](https://fastapi.tiangolo.com/) and [Pydantic](https://pydantic.dev/) for high performance and automatic data validation.
-   **🔍 Full Observability**: Deep insights into your agent's performance and behavior with integrated tracing support for [Logfire](https://logfire.pydantic.dev/) and [Langfuse](https://langfuse.com/).
-   **🔧 Rich CLI Toolkit**: Manage your services with a command-line interface built with [Typer](https://typer.tiangolo.com/), including commands to run the server, Temporal workers, and other utilities.
-   **📦 Extensible by Design**: Easily add new workflows, agents, API endpoints, and utility functions to suit your project's needs.

## 🏗️ Architecture Overview

AntGent is structured in distinct layers, promoting separation of concerns and modularity:

1.  **API Layer (`FastAPI`)**: Exposes RESTful endpoints for interacting with the system. This is the entry point for starting new workflows, checking their status, and retrieving results.
2.  **Orchestration Layer (`Temporal`)**:
    -   **Workflows**: Define the high-level logic and sequence of operations. Workflows are deterministic, fault-tolerant, and can run for seconds or years.
    -   **Activities**: Implement the actual business logic, such as calling an LLM, accessing a database, or interacting with an external API. Activities are where side effects happen.
    -   **Workers**: Daemons that host and execute your workflow and activity code.
3.  **Agent Layer**: Contains the core AI logic. Agents encapsulate a specific task, managing prompts, interacting with LLMs, and parsing the output.
4.  **Configuration Layer**: A centralized, Pydantic-based configuration system allows you to manage settings for all components (Temporal, LLMs, server, etc.) through YAML files and environment variables.

## 🚀 Getting Started

### Prerequisites

-   Python 3.12+
-   A running [Temporal Server](https://docs.temporal.io/self-hosted-guide/run-temporal). The easiest way to get started is with `temporal server start-dev`.
-   Access to an LLM provider (e.g., an OpenAI API key).

### 1. Installation

Clone the repository and install the dependencies using `uv`:

```bash
git clone https://github.com/your-username/antgent.git
cd antgent
uv venv
uv sync -d
```

### 2. Configuration

AntGent uses a YAML file for configuration. Copy the example and customize it for your environment:

1.  Create a `localconfig.yaml` file.
2.  Configure your Temporal server address and LLM API keys.

**Example `localconfig.yaml`:**
```yaml
# temporalio configuration
temporalio:
  host: "127.0.0.1:7233"
  namespace: "default"
  workers:
    - name: "antgent-workflow"
      queue: "antgent-queue"
      workflows:
        - "antgent.workflows.summarizer:TextSummarizerWorkflow"
    - name: "antgent-activities"
      queue: "antgent-queue-activity"
      activities:
        - "antgent.workflows.summarizer:run_summarizer_activity"

# LLM provider configuration (using litellm)
llms:
  litellm:
    api_key: "sk-..." # Your OpenAI key, for example
  # You can define aliases for models
aliases:
  root:
    "default-summarizer": "gemini/gemini-1.5-pro-latest"
    "fast-summarizer": "groq/llama3-8b-8192"

# Agent-specific configurations can override defaults
agents:
  root:
    SummaryAgent:
      model: "default-summarizer" # Use the alias
```

### 3. Run the Services

You need to run two separate processes: the Temporal Worker and the API Server.

**Terminal 1: Start the Temporal Worker**
```bash
uv run antgent looper --config=localconfig.yaml
```
This worker listens for tasks on the queues defined in your config and executes your workflows and activities.

**Terminal 2: Start the API Server**
```bash
uv run antgent server --config localconfig.yaml
```
The API server will be available at `http://127.0.0.1:8000`. You can access the auto-generated documentation at `http://127.0.0.1:8000/docs`.

## 💻 Usage Example: Text Summarization

With the server running, you can start a summarization workflow via the API.

Use `curl` to submit a text for summarization:
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/workflows/summarizer' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "context": {
      "content": "The James Webb Space Telescope (JWST) is a space telescope designed primarily to conduct infrared astronomy. As the largest optical telescope in space, its high resolution and sensitivity allow it to view objects too old, distant, or faint for the Hubble Space Telescope.",
      "to_language": "en"
    },
    "llm_input": ""
  }'
```

This will return a `workflow_id`. You can use this ID to check the status and get the result:

```bash
# Replace {workflow_id} with the ID from the previous step
curl 'http://127.0.0.1:8000/api/workflows/summarizer/{workflow_id}'
```

Keep polling this endpoint until the status is `COMPLETED`, and the result will contain the generated summaries.

## 🛠️ Development

### Running Tests
To run the full test suite:
```bash
make test
```

### Linting and Formatting
This project uses `ruff` for linting and `black` for formatting (both integrated into `ruff`).

To check for issues:
```bash
make check
```

To automatically fix issues:
```bash
make fix
```

### Creating a New Workflow

1.  **Define Models**: Create Pydantic models for your workflow's input and output in a `models.py` file.
2.  **Write Activities**: Implement the core logic in `activities.py`. An activity can be any function that performs I/O, calls an API, etc.
3.  **Write the Workflow**: In `workflows.py`, define a class inheriting from `BaseWorkflow`. Use `workflow.execute_activity()` to orchestrate your activities.
4.  **Register Components**: Add your new workflow and activities to `localconfig.yaml` under the appropriate worker.
5.  **Create API Endpoint**: Add a new endpoint in the `antgent/server/api/` directory to trigger your workflow.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and add tests.
4.  Ensure all tests and linting checks pass (`make check`).
5.  Commit your changes and push to your branch.
6.  Open a Pull Request with a clear description of your changes.

Please adhere to the coding conventions outlined in `.aider/python-convention.md`.

## 📄 License

This project is licensed under the terms of the license agreement found in the `LICENSE` file.
