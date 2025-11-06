from temporalio import activity

from antgent.config import config
from antgent.models.agent import AgentConfig


@activity.defn
async def get_agent_configs() -> dict[str, AgentConfig]:
    """Activity to load agent configurations."""
    return config().agents


@activity.defn
def echo(message: str) -> str:
    """A simple echo activity."""
    activity.logger.info(f"Echoing message: {message}")
    return f"Echo: {message}"


@activity.defn
async def aecho(message: str) -> str:
    """A simple async echo activity."""
    activity.logger.info(f"Async echoing message: {message}")
    return f"Async echo: {message}"
