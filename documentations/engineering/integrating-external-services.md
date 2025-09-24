# Integrating with External Services

Our project often needs to interact with external APIs and services. To keep these interactions clean, reusable, and efficient, we follow a standardized pattern for creating service clients.

## The Client Factory Pattern

We use a "client factory" pattern, where a function is responsible for creating and caching an instance of a client. This is implemented in `antgent/clients.py`.

**Core Components:**
-   **Client Class**: A class that encapsulates the logic for making requests to an external service. It should inherit from `ant31box.client.base.BaseClient` if it's a simple HTTP client.
-   **Factory Function**: A function decorated with `@functools.cache` that instantiates and returns the client. The caching ensures that we reuse the same client instance (and its underlying connection pool) throughout the application, which is much more efficient.

### Example: The `AsyncOpenAI` Client

Let's look at the client for OpenAI.

**The Factory Function (`antgent/clients.py`)**

```python
# antgent/clients.py
from functools import cache
from openai import AsyncOpenAI
import logfire

from antgent.config import config
from antgent.models.agent import LLMsConfigSchema

@cache
def openai_aclient(project_name: str = "openai", llms: LLMsConfigSchema | None = None) -> AsyncOpenAI:
    """Create a OpenAI instance with the given api_key
    It cache the answer for the same api_key
    use openai.cache_clear() to clear the cache
    """
    if llms is None:
        llms = config().llms

    project = llms.get_project(project_name)
    if project is None:
        # use default with ENV
        client = AsyncOpenAI()
    else:
        client = AsyncOpenAI(
            api_key=project.api_key,
            organization=project.organization_id,
            project=project.project_id,
            base_url=project.url,
        )
    logfire.instrument_openai(client)
    return client
```

**How it works:**
-   `@cache`: The first time `openai_aclient()` is called with a specific `project_name`, it creates a new `AsyncOpenAI` instance using the current configuration. This instance is then stored in a cache.
-   Subsequent calls to `openai_aclient()` with the same arguments will return the cached instance directly, without re-reading the configuration or creating a new object.

## How to Add a New Client

Follow these steps to integrate a new external service.

### Step 1: Create the Client Class

Create a new file, e.g., `antgent/my_service_client.py`. In this file, define a class for your new service. If it's a REST API, inheriting from `BaseClient` is recommended.

```python
# antgent/my_service_client.py
from ant31box.client.base import BaseClient

class MyServiceClient(BaseClient):
    def __init__(self, endpoint: str, api_key: str):
        super().__init__(endpoint=endpoint, client_name="myservice")
        self.api_key = api_key

    def headers(self, content_type="json", extra=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        return super().headers(content_type, extra=headers)

    async def get_some_data(self, item_id: int) -> dict:
        url = self._url(f"/items/{item_id}")
        resp = await self.session.get(url, headers=self.headers())
        resp.raise_for_status()
        return await resp.json()
```

### Step 2: Add Configuration

Add a configuration schema for your new service in `antgent/config.py`.

```python
# antgent/config.py
from ant31box.config import BaseConfig
import ant31box.config
from pydantic import Field

class MyServiceConfigSchema(BaseConfig):
    endpoint: str = Field("https://api.myservice.com")
    api_key: str = Field(...)

class ConfigSchema(ant31box.config.ConfigSchema):
    # ...
    my_service: MyServiceConfigSchema = Field(default_factory=MyServiceConfigSchema)
```

### Step 3: Create the Factory Function

Add a factory function for your new client in `antgent/clients.py`.

```python
# antgent/clients.py
# ... other imports
from antgent.my_service_client import MyServiceClient

@cache
def my_service_client() -> MyServiceClient:
    """Creates and caches a MyServiceClient instance."""
    cfg = config().my_service
    return MyServiceClient(endpoint=cfg.endpoint, api_key=cfg.api_key)
```

### Step 4: Use the Client

Now, anywhere in the application, you can get an instance of your client by calling the factory function.

```python
from antgent.clients import my_service_client

async def some_function():
    client = my_service_client()
    data = await client.get_some_data(123)
    # ... do something with data
```

This pattern keeps service integration clean, ensures efficient resource use through caching, and centralizes configuration.
