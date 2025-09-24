# Configuration Management

The antgent framework uses a powerful and flexible configuration system built on `pydantic-settings`. This allows for type-safe configuration management from multiple sources, ensuring that your application is easy to configure for different environments (development, testing, production).

## Configuration Hierarchy

Configuration is loaded from the following sources, in order of precedence (lower numbers are overridden by higher numbers):

1.  **Default Schema Values**: Defaults defined directly in the Pydantic model schemas in `antgent/config.py`.
2.  **YAML Configuration File**: A YAML file can be specified to provide configuration values.
3.  **Environment Variables**: Any configuration value can be overridden by an environment variable.

## The `ConfigSchema`

The main configuration structure is defined in `antgent/config.py` within the `ConfigSchema` class. This class uses nested Pydantic models to organize configuration by domain.

**Example: `ConfigSchema` structure**
```python
# antgent/config.py
import ant31box.config
from pydantic import Field
from pydantic_settings import SettingsConfigDict

# ... other schema imports like TemporalCustomConfigSchema, S3ConfigSchema

class ConfigSchema(ant31box.config.ConfigSchema):
    _env_prefix = "ANTGENT"
    model_config = SettingsConfigDict(
        env_prefix=f"{ENVPREFIX}_",
        env_nested_delimiter="__",
        # ...
    )
    name: str = Field(default="antgent")
    # server: FastAPIConfigSchema is inherited from ant31box.config.ConfigSchema
    temporalio: TemporalCustomConfigSchema = Field(default_factory=TemporalCustomConfigSchema)
    s3: S3ConfigSchema = Field(default_factory=S3ConfigSchema)
    # ... and other nested schemas like 'llms', 'agents', etc.
```

### Environment Variables

You can override any configuration setting using an environment variable. The variable name is constructed based on the schema structure:

-   It starts with the prefix `ANTGENT_`.
-   Nested keys are separated by a double underscore `__`.
-   The variable name is case-insensitive.

**Examples:**

-   To set the server port: `export ANTGENT_SERVER__PORT=8001`
-   To set the Temporal host: `export ANTGENT_TEMPORALIO__HOST=temporal.prod.svc.cluster.local`
-   To set the S3 bucket: `export ANTGENT_S3__BUCKET=my-production-bucket`

## Loading Configuration

The configuration is loaded via the `config()` function in `antgent/config.py`.

```python
from antgent.config import config

# Load config from default path or environment variables
_config = config()

# Load config from a specific YAML file
_config_from_file = config(path="/path/to/my/config.yaml")
```

The CLI commands, like `antgent server`, also provide an option to specify a configuration file using the `-c` or `--config` flag.

## Adding a New Configuration Section

To add configuration for a new agent or service, follow these steps:

1.  **Create a new Pydantic Schema**: Define a `BaseModel` for your new configuration section.

    ```python
    from pydantic import BaseModel, Field

    class MyAgentConfigSchema(BaseModel):
        api_key: str = Field(..., description="API key for the agent's service.")
        timeout: int = Field(default=60, description="Request timeout in seconds.")
    ```

2.  **Add the Schema to the Main `ConfigSchema`**: Add your new schema as a field in `antgent/config.py:ConfigSchema`.

    ```python
    # antgent/config.py
    # ... other imports
    import ant31box.config

    class ConfigSchema(ant31box.config.ConfigSchema):
        # ... other fields
        my_agent: MyAgentConfigSchema = Field(default_factory=MyAgentConfigSchema)
    ```

3.  **Access Your Configuration**: You can now access your new configuration settings from the global `config` object.

    ```python
    from antgent.config import config

    agent_config = config().my_agent
    print(agent_config.api_key)
    ```

4.  **Set via Environment Variables**: The new settings are automatically available via environment variables.
    ```bash
    export ANTGENT_MY_AGENT__API_KEY="your-secret-key"
    ```

This structured approach ensures that configuration is type-checked, self-documenting, and easily managed across different deployment environments.
