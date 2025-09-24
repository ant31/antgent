# Managing Data Models (Pydantic)

Data models are a cornerstone of the antgent framework. We use [Pydantic](https://docs.pydantic.dev/) extensively to define the structure of data for agent inputs and outputs, API requests and responses, and workflow contexts. This ensures data validation, type safety, and makes the code more self-documenting.

This guide outlines best practices for creating and maintaining Pydantic models in this project.

## Core Principles

-   **Clarity and Explicitness**: Models should be easy to understand. Use descriptive names for models and fields.
-   **Validation, Not Just Structure**: Pydantic is more than just a data container. Use its validation features (e.g., `ge`, `le` for numbers, `max_length` for strings) where appropriate.
-   **Single Source of Truth**: Define a model once and reuse it across agents, workflows, and API layers. Avoid duplicating model definitions.

## Best Practices

### Field Definitions

Always use `pydantic.Field` to define model attributes. This provides a consistent place to add metadata like descriptions, default values, and validation rules.

-   **Descriptions are Mandatory**: Every field must have a `description`. This is used to automatically generate documentation for APIs and helps other developers understand the purpose of each field.
-   **Required Fields**: For fields that must be provided, use `...` as the first argument to `Field`.
-   **Optional Fields**: For optional fields, provide a `default` or `default_factory`. Use `| None` for the type hint.

**Example:**
```python
# antgent/agents/summarizer/models.py
from pydantic import BaseModel, Field

class SummaryInput(BaseModel):
    content: str = Field(...)
    feedbacks: list[str] = Field(
        default_factory=list, description="List of feedbacks for creating the less verbose text"
    )
    to_language: str = Field(
        "de", description="The language to translate the summary to. E.g., 'en' for English, 'de' for German."
    )
```

### Type Hinting Style

Use modern Python type hints (Python 3.10+).
-   Use `|` for unions (e.g., `int | str`) instead of `typing.Union`.
-   Use built-in generic types (e.g., `list[int]`) instead of `typing.List`.
-   Use `X | None` for optional types (e.g., `str | None`) instead of `typing.Optional`.

### Model Organization

-   **Agent-Specific Models**: Models used exclusively by a single agent should be defined in a `models.py` file within that agent's directory (e.g., `antgent/agents/summarizer/models.py`).
-   **Shared Models**: Models that are shared across multiple workflows or represent core data structures for the application are defined in `antgent/models/`.

### Versioning and Evolution

When you need to change a model (e.g., add a field, change a type), consider the impact on backwards compatibility, especially for workflow inputs and API endpoints.

-   **Adding New Fields**: If you add a new field, provide a `default` value to ensure that old data (e.g., from a persisted workflow execution) can still be parsed by the new model version.
-   **Changing Field Types**: This is a breaking change. If you must do this, consider creating a new model version and planning for a migration.
-   **Removing Fields**: This is also a breaking change. Before removing a field, ensure it is no longer being used anywhere.

By adhering to these practices, we maintain a clear, robust, and maintainable data layer throughout the application.
