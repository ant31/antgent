# Testing Strategy

A robust testing strategy is crucial for maintaining code quality and ensuring the reliability of our agents and workflows. This guide outlines the best practices for writing tests in this project using `pytest`.

## Core Principles

-   **Unit Tests**: Test individual components (like a specific function or agent method) in isolation.
-   **Integration Tests**: Test how multiple components work together (e.g., an agent's full workflow, an API endpoint triggering a workflow).
-   **Isolation**: Tests should be independent and not rely on the state of other tests. Use mocks and fixtures to isolate the system under test.

## Writing Tests with `pytest`

### Fixtures for Setup and Teardown

Fixtures are functions decorated with `@pytest.fixture` that provide a fixed baseline for tests. They are ideal for setting up resources like API clients or test data.

**Example: Creating a test client for the API server**
A `client` fixture is available in `tests/conftest.py` for testing API endpoints.

```python
# Example test
from fastapi.testclient import TestClient

def test_some_api_endpoint(client: TestClient):
    """Tests an API endpoint."""
    response = client.get("/api/workflows/types")
    assert response.status_code == 200
    # ... more assertions
```
Here, the `client` fixture is automatically injected into the test function by `pytest`.

### Mocking with `mocker`

We use the `pytest-mock` plugin, which provides the `mocker` fixture, to replace parts of our system with mock objects. This is essential for isolating tests from external dependencies like LLM APIs, databases, or Temporal activities.

**Example: Mocking an activity**
To test a workflow's logic without executing the actual activity, you can mock the activity function.

```python
# In tests/temporal/test_activities.py
from typing import Any
from temporalio import activity

@activity.defn(name="aecho")
async def aecho_mocked(model: dict[str, Any]) -> dict[str, Any]:
    _ = model
    return {"greeting": "Hello from mocked activity!"}
```
This mock can then be passed to a worker in a test environment to override the real activity.

### Parameterization

Use `@pytest.mark.parametrize` to run the same test function with different inputs and expected outputs. This is highly efficient for testing various scenarios and edge cases.

**Example: Testing a utility function with different inputs**
```python
# From tests/test_aliases.py

@pytest.mark.parametrize("loop_setup, problematic_alias, expected_loop_path_str", [
    ({"a": "a"}, "a", "a -> a"),
    ({"a": "b", "b": "a"}, "a", "a -> b -> a"),
    ({"a": "b", "b": "c", "c": "a"}, "a", "a -> b -> c -> a"),
])
def test_resolve_circular_dependency(empty_resolver, loop_setup, problematic_alias, expected_loop_path_str):
    resolver = empty_resolver
    for k, v in loop_setup.items():
        resolver[k] = v
    with pytest.raises(ValueError, match=f"Circular dependency detected: {expected_loop_path_str}"):
        resolver.resolve(problematic_alias)
```

### Testing Asynchronous Code

For testing `async` functions, decorate the test function with `@pytest.mark.asyncio`. `pytest` will then run it in an asyncio event loop.

```python
# From tests/temporal/test_activities.py
import pytest
from temporalio.client import Client

@pytest.mark.asyncio
async def test_echo_workflow(client: Client):
    # ... test logic using await
```

By following these patterns, you can write clean, effective, and maintainable tests that contribute to the overall stability of the antgent project.
