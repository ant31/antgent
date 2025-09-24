# Python Coding Style and Conventions

This document outlines the coding conventions to be followed in this project. Adhering to these conventions ensures consistency, readability, and maintainability of the codebase.

## Python Style

-   **Version**: Write code compatible with Python 3.12 features and style.
-   **Formatting & Linting**: We use `ruff` for all formatting, linting, and import sorting. Adhere to the configurations defined in `pyproject.toml`.
    -   To format your code, run: `make format`
    -   To sort imports, run: `make isort`
    -   To check for issues, run: `make check`
    -   Most issues can be fixed automatically by running: `make fix`
-   **Naming**:
    -   Use `snake_case` for variables, functions, methods, and modules.
    -   Use `PascalCase` for classes.
    -   Use `UPPER_SNAKE_CASE` for constants.
-   **Docstrings**: Write clear and concise docstrings for all public modules, classes, functions, and methods. Google style docstrings are preferred.
-   **Import conditions**: Do not safeguard imports to check if a library is not installed. If it's not installed then the program will fail as expected. This is part of dependency management.
-   **Code organization**: Split code into modules and packages for various features. Aim for short, focused Python files.

### Don't Safeguard Imports
*  **Bad:**
   ```python
   try:
       import pydot
   except ImportError:
       pydot = None
   ```
* **Good:**
   ```python
   import pydot
   ```

## Code Comments

-   **Focus**: Comments should explain the *why* behind the code, clarify complex logic, or document non-obvious decisions. They should not just describe *what* the code is doing.
-   **Timelessness**: Write comments that will remain true and relevant over time. Avoid comments that refer to the development process, specific points in time, or temporary states.
-   **Avoid Redundancy**: Do not comment on obvious code. Good code should be largely self-documenting.

**Examples:**

*   **Bad:**
    ```python
    # Added this check because the API sometimes returns null - need to verify if still needed
    if data is not None:
        process(data)

    # TODO: Refactor this later
    result = complex_calculation(x, y, z)

    # Quick fix for bug #123
    value = adjust_value(value)
    ```
*   **Good:**
    ```python
    # The external API (v1.2) occasionally returns null for this field,
    # so we explicitly check for None before processing.
    if data is not None:
        process(data)

    # This calculation implements the Frobnicate algorithm (see paper XYZ)
    # to determine the optimal widget alignment.
    result = complex_calculation(x, y, z)

    # Adjust the value to compensate for sensor drift observed in model T-800.
    value = adjust_value(value)
    ```

## Type Hinting

-   **Mandatory**: All function signatures, method signatures, and variables where the type isn't immediately obvious should have type hints.
-   **Style**: Use Python 3.10+ style type hints:
    -   Use built-in generic types (e.g., `list[int]`, `dict[str, float]`) instead of importing from `typing` (`List`, `Dict`) where possible.
    -   Use the `|` operator for unions (e.g., `int | str`) instead of `typing.Union`.
    -   Use `X | None` for optional types (e.g., `str | None`) instead of `typing.Optional`.

## Pydantic (v2)

-   **Usage**: Use Pydantic models for data validation, serialization/deserialization, API request/response models, and complex configuration structures. Avoid using Pydantic for simple, internal dictionaries where the structure is trivial or highly dynamic without a clear schema.
-   **Field Definitions**:
    -   Always initialize fields using `Field()`.
    -   Provide a `default=` value or `default_factory=` for optional fields within `Field()`. Example: `my_field: str | None = Field(default=None, description="...")`.
    -   Use `Field(..., description="...")` for required fields. Example: `required_field: int = Field(..., description="This field must be provided.")`.
    -   Prefer providing a default value directly (e.g., `count: int = 0`) or via `Field(default=...)` over making a field required (`Field(...)`) unless it's semantically necessary for the field to be explicitly provided.
    -   Include a `description=` for all fields to improve clarity.
-   **External APIs**: When parsing data from external APIs that might change, configure models to allow extra fields to prevent errors on unexpected data:
    ```python
    from pydantic import BaseModel, ConfigDict

    class ExternalData(BaseModel):
        model_config = ConfigDict(extra='allow')

        known_field: str
        # ... other known fields
    ```
-   **Methods**: Use `model_validate()` for parsing/validation and `model_dump()` for serialization instead of the deprecated V1 methods (`parse_obj`, `dict`, `json`).

## Pytest

-   **Fixtures**: Use fixtures for setting up test preconditions (e.g., database connections, client instances, sample data) and for teardown. Prefer fixtures over global constants for test setup.
-   **Parameterization**: Use `@pytest.mark.parametrize` to test the same logic with multiple different inputs and expected outputs efficiently.
-   **Test Granularity**: Write small, focused tests. Each test should ideally verify one specific aspect or behavior. Avoid creating large tests that cover many different use cases.
-   **Flexibility**: Design tests to be resilient to minor, unrelated code changes. Instead of hardcoding exact output values (especially for complex objects or LLM responses), consider:
    -   Checking for the presence of specific keys or attributes.
    -   Validating the *type* of the result.
    -   Asserting that values fall within expected ranges or match certain patterns.
    -   Mocking dependencies effectively.

## SQL Databases

-   **Table Naming**: Use singular nouns for table names (e.g., `user`, `order`, `product`).

## General

-   **Logging**: Use the standard `logging` module. Configure loggers appropriately for different modules.
-   **Error Handling**: Use specific exception types where possible. Handle exceptions gracefully and provide informative error messages.
-   **Asynchronous Code**: Use `async` and `await` consistently for I/O-bound operations.
