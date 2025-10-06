import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

from agents import (
    Agent,
    Model,
    OpenAIChatCompletionsModel,
    OpenAIResponsesModel,
    RunContextWrapper,
)
from agents.extensions.models.litellm_model import LitellmModel

from antgent.agents.config_resolver import ConfigResolverMixin
from antgent.agents.message_handler import MessageHandlerMixin
from antgent.agents.runner import AgentRunnerMixin
from antgent.aliases import Aliases, AliasResolver
from antgent.clients import openai_aclient
from antgent.models.agent import (
    AgentConfig,
    AgentFrozenConfig,
    AgentRunMetadata,
    LLMsConfigSchema,
    ModelProvidersConfig,
    PrepareRun,  # Re-export for backward compatibility
    TLLMInput,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")

MaybeAwaitable = Awaitable[T] | T  # type: ignore[valid-type]

__all__ = ["BaseAgent", "PrepareRun", "TLLMInput"]


class BaseAgent[TContext, TOutput](ConfigResolverMixin, MessageHandlerMixin, AgentRunnerMixin[TContext, TOutput]):
    name_id: str = "Base"
    default_config: AgentConfig
    agent_config: AgentFrozenConfig[TOutput, TOutput]
    alias_resolver: AliasResolver | None = Aliases
    llms_conf: LLMsConfigSchema | None = None
    provider_config: ModelProvidersConfig | None = None

    def __init__(
        self,
        conf: AgentConfig | dict[str, AgentConfig] | None = None,
        *,
        metadata: AgentRunMetadata | None = None,
        alias_resolver: AliasResolver | None = None,
    ) -> None:
        self.metadata = metadata
        self.alias_resolver = alias_resolver or Aliases
        self.conf = self.update_config(conf)
        self._max_tokens: int | None = None

    @abstractmethod
    def prompt(self) -> str | Callable[[RunContextWrapper[TContext], Agent[TContext]], MaybeAwaitable[str]] | None:
        """
        Returns the prompt for the agent. This can be a static string or a callable that takes the context and
        agent as arguments and returns a string or an awaitable string.
        """

    @property
    def model(self):
        if self.alias_resolver:
            return self.alias_resolver.resolve(self.conf.model)
        return self.conf.model

    @classmethod
    def set_alias_resolver(cls, resolver: AliasResolver) -> None:
        cls.alias_resolver = resolver

    @classmethod
    def set_provider_config(cls, provider_config: ModelProvidersConfig) -> None:
        """Set the provider configuration for this agent class."""
        cls.provider_config = provider_config

    def get_sdk_model(self) -> Model:
        logger.info(
            "[%s] Using model: %s (client=%s, api_mode=%s)",
            self.name_id,
            self.model,
            self.conf.client,
            self.conf.api_mode,
        )
        if self.conf.api_mode == "response":
            return OpenAIResponsesModel(
                model=self.model, openai_client=openai_aclient(self.conf.client, llms=self.llms_conf)
            )
        if self.conf.client == "openai":
            return OpenAIChatCompletionsModel(
                model=self.model, openai_client=openai_aclient(self.conf.client, llms=self.llms_conf)
            )
        return LitellmModel(model=self.model, api_key=self.conf.api_key, base_url=self.conf.base_url)

    def agent(self) -> Agent[TContext]:
        model = self.get_sdk_model()
        logger.debug("Agent: %s", self.conf.name)
        logger.debug("Model: %s", self.model)
        logger.debug("Model class: %s", model)
        logger.debug("Model settings: %s", self.conf.model_settings)
        return Agent(
            name=self.conf.name,
            model=self.get_sdk_model(),
            instructions=self.prompt(),
            output_type=self.agent_config.get_structured_cls(),
            model_settings=self.conf.model_settings,
        )

    async def workflow(self, llm_input: TLLMInput, context: TContext) -> TOutput | None:
        return await self.run(self.agent(), llm_input, context)
