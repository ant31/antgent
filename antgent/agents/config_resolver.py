import logging
from typing import TYPE_CHECKING, Any

from antgent.models.agent import AgentConfig, ModelProvidersConfig, ProviderMapping

if TYPE_CHECKING:
    from antgent.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ConfigResolverMixin:
    """Mixin for resolving agent configuration."""

    def _resolve_model_name(self: "BaseAgent", model_name: str) -> str:
        """Resolves model name through alias resolver if available."""
        if not self.alias_resolver:
            return model_name

        resolved = self.alias_resolver.resolve(model_name)
        if resolved != model_name:
            logger.info("[%s] Alias resolved: %s -> %s", self.name_id, model_name, resolved)
        return resolved

    @classmethod
    def _find_provider_mapping(
        cls: type["BaseAgent"], model_name: str, provider_config: ModelProvidersConfig
    ) -> ProviderMapping | None:
        """Finds matching provider mapping for the given model name."""
        for mapping in provider_config.mappings:
            if model_name.startswith(mapping.prefix):
                logger.debug("[%s] Matched prefix '%s' for model '%s'", cls.name_id, mapping.prefix, model_name)
                return mapping

        logger.debug("[%s] No prefix match found for '%s', using default provider settings", cls.name_id, model_name)
        return None

    @classmethod
    def _apply_provider_setting(
        cls: type["BaseAgent"],
        setting_name: str,
        result_dict: dict[str, Any],
        config_overrides: dict[str, Any],
        *,
        matched_mapping: ProviderMapping | None,
        provider_config: ModelProvidersConfig,
    ):
        """Applies a single provider setting (client or api_mode) to result_dict."""
        if setting_name in config_overrides:
            logger.debug(
                "[%s] Using explicit %s override: %s", cls.name_id, setting_name, config_overrides[setting_name]
            )
            return

        if matched_mapping:
            value = getattr(matched_mapping, setting_name)
            result_dict[setting_name] = value
            logger.info("[%s] Applying %s from matched mapping: %s", cls.name_id, setting_name, value)
        else:
            value = getattr(provider_config.default, setting_name)
            result_dict[setting_name] = value
            logger.info("[%s] Applying default %s: %s", cls.name_id, setting_name, value)

    def update_config(self: "BaseAgent", conf: AgentConfig | dict[str, AgentConfig] | None = None) -> AgentConfig:
        if isinstance(conf, dict):
            conf = conf.get(self.name_id, None)

        # Start with default config
        result_dict = self.default_config.model_dump()

        # Get overrides from provided config
        config_overrides = {}
        if conf:
            config_overrides = conf.model_dump(exclude_unset=True, exclude_defaults=True)
        logger.debug("[%s] Config overrides: %s", self.name_id, config_overrides)
        # Determine and resolve model name
        model_name = config_overrides.get("model", result_dict.get("model", ""))
        logger.info("[%s] Configuring agent with model: %s", self.name_id, model_name)
        resolved_model = self._resolve_model_name(model_name)
        if resolved_model != model_name:
            logger.info("[%s] Model alias resolved: %s -> %s", self.name_id, model_name, resolved_model)
        model_name = resolved_model

        # Use injected provider config or fall back to default
        provider_config = self.provider_config or ModelProvidersConfig()
        logger.debug("[%s] Provider config has %s prefix mappings", self.name_id, len(provider_config.mappings))
        logger.debug("[%s] Provider config: %s", self.name_id, provider_config)
        matched_mapping = self._find_provider_mapping(model_name, provider_config)

        # Apply provider settings
        self._apply_provider_setting(
            "client", result_dict, config_overrides, matched_mapping=matched_mapping, provider_config=provider_config
        )
        self._apply_provider_setting(
            "api_mode", result_dict, config_overrides, matched_mapping=matched_mapping, provider_config=provider_config
        )

        # Finally, apply all config overrides
        result_dict.update(config_overrides)

        final_config = AgentConfig.model_validate(result_dict)
        logger.info(
            "[%s] Final configuration: model=%s, client=%s, api_mode=%s",
            self.name_id,
            final_config.model,
            final_config.client,
            final_config.api_mode,
        )

        return final_config
