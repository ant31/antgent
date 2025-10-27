import json

from antgent.models.agent import DynamicAgentConfig


def parse_dynamic_agent_config(agent_config_json: str | None) -> DynamicAgentConfig | None:
    """
    Parses a DynamicAgentConfig from a JSON string.
    Returns a DynamicAgentConfig object, or None if empty.
    """
    if not agent_config_json or agent_config_json == "null":
        return None

    try:
        config_dict = json.loads(agent_config_json)
        validated = DynamicAgentConfig.model_validate(config_dict)

        # If no overrides specified, return None
        if not validated.model and not validated.aliases and not validated.agents:
            return None

        # Return as Pydantic model
        return validated
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for agent_config_json: {e}") from e
    except Exception as e:
        raise ValueError(f"Invalid DynamicAgentConfig structure: {e}") from e
