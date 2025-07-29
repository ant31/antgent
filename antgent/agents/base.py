import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

from agents import (
    Agent,
    Model,
    OpenAIChatCompletionsModel,
    OpenAIResponsesModel,
    RunContextWrapper,
    Runner,
    RunResult,
    TResponseInputItem,
    custom_span,
)
from agents.extensions.models.litellm_model import LitellmModel
from litellm.utils import get_max_tokens, token_counter

from antgent.clients import openai_aclient
from antgent.models.agent import (
    AgentConfig,
    AgentFrozenConfig,
    AgentRunMetadata,
    LLMsConfigSchema,
    PrepareRun,
    TLLMInput,
)
from antgent.utils.aliases import Aliases, AliasResolver

logger = logging.getLogger(__name__)
T = TypeVar("T")

MaybeAwaitable = Awaitable[T] | T


class ContextTooLargeError(ValueError): ...


class BaseAgent[TContext, TOutput]:
    name_id: str = "Base"
    default_config: AgentConfig
    agent_config: AgentFrozenConfig
    alias_resolver: AliasResolver | None = Aliases
    llms_conf: LLMsConfigSchema | None = None

    def __init__(
        self, conf: AgentConfig | dict[str, AgentConfig] | None = None, metadata: AgentRunMetadata | None = None
    ) -> None:
        self.metadata = metadata
        self.conf = self.update_config(conf)
        self._max_tokens: int | None = None

    @classmethod
    def update_config(cls, conf: AgentConfig | dict[str, AgentConfig] | None = None) -> AgentConfig:
        if isinstance(conf, dict):
            conf = conf.get(cls.name_id, None)
        if conf:
            updated = conf.model_dump(exclude_defaults=True, exclude_unset=True)
            default = cls.default_config.model_dump()
            # Merge values
            default.update(updated)
            conf = AgentConfig.model_validate(default)
        else:
            conf = cls.default_config
        return conf

    @abstractmethod
    def prompt(self) -> str | Callable[[RunContextWrapper[TContext], Agent[TContext]], MaybeAwaitable[str]] | None:
        """
        Returns the prompt for the agent. This can be a static string or a callable that takes the context and
        agent as arguments and returns a string or an awaitable string.
        """
        pass

    @property
    def model(self):
        if self.alias_resolver:
            return self.alias_resolver.resolve(self.conf.model)
        return self.conf.model

    @classmethod
    def set_alias_resolver(cls, resolver: AliasResolver) -> None:
        cls.alias_resolver = resolver

    def get_sdk_model(self) -> Model:
        if self.conf.client in {"litellm", "litellm_proxy"}:
            return LitellmModel(model=self.model, api_key=self.conf.api_key, base_url=self.conf.base_url)
        if self.conf.api_mode == "response":
            return OpenAIResponsesModel(
                model=self.model, openai_client=openai_aclient(self.conf.client, llms=self.llms_conf)
            )
        return OpenAIChatCompletionsModel(
            model=self.model, openai_client=openai_aclient(self.conf.client, llms=self.llms_conf)
        )

    def agent(self) -> Agent[TContext]:
        return Agent(
            name=self.conf.name,
            model=self.get_sdk_model(),
            instructions=self.prompt(),
            output_type=self.agent_config.get_structured_cls(),
            model_settings=self.conf.model_settings,
        )

    def add_inputs(self, llm_input: TLLMInput, messages: list[TResponseInputItem] | None) -> list[TResponseInputItem]:
        if messages is None:
            messages = []
        if isinstance(llm_input, list):
            messages.extend(llm_input)
        elif isinstance(llm_input, str) and llm_input:
            messages.append({"content": llm_input, "role": "user"})
        return messages

    async def prep_input(self, llm_input: TLLMInput, ctx: TContext) -> PrepareRun[TContext]:
        if not isinstance(llm_input, str) and not isinstance(llm_input, list):
            raise ValueError(f"Input must be a string or list of TResponseInputItem, got {type(llm_input)}")
        return PrepareRun(llm_input=cast(TLLMInput, llm_input), context=ctx, short_cut=False)

    async def prep_response(self, response: RunResult | None, ctx: TContext) -> RunResult | None:
        _ = ctx
        if response is None:
            return None
        return response

    async def run_result(
        self, agent, llm_input: TLLMInput, context: TContext, check_tokens: bool = False, **kwargs
    ) -> RunResult | None:
        with custom_span("Prepare input"):
            prep_run = await self.prep_input(llm_input, context)
            if prep_run.short_cut:
                logger.info("ShortCut requested: stoping the run")
                return None
            if check_tokens and self.max_tokens > 0 and self.count_tokens(prep_run.llm_input) > self.max_tokens:
                raise ContextTooLargeError(f"Input too large: {self.count_tokens(prep_run.llm_input)} tokens")
        res = await Runner.run(agent, input=prep_run.llm_input, context=prep_run.context, **kwargs)
        return await self.prep_response(res, context)

    async def run(
        self, agent, llm_input: TLLMInput, context: TContext, check_tokens: bool = False, **kwargs
    ) -> TOutput | None:
        res = await self.run_result(agent, llm_input, context, check_tokens, **kwargs)
        if res is None:
            return None
        return res.final_output

    async def workflow(self, llm_input: TLLMInput, context: TContext) -> TOutput | None:
        return await self.run(self.agent(), llm_input, context)

    def count_tokens(self, content) -> int:
        return token_counter(self.model, messages=content)

    @property
    def max_tokens(self) -> int:
        if self._max_tokens is None:
            maxtokens = get_max_tokens(self.model)
            if maxtokens is None:
                maxtokens = 0
            if self.conf.max_input_tokens and maxtokens > 0:
                maxtokens = min(self.conf.max_input_tokens, maxtokens)
            self._max_tokens = maxtokens
        return self._max_tokens
