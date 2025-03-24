from abc import abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar, Literal, Self, TypeVar, cast

import tiktoken
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
from agents.handoffs import Handoff
from agents.lifecycle import AgentHooks
from agents.model_settings import ModelSettings

# from agents.guardrails import Guardrail
from agents.tool import MaybeAwaitable, Tool
from pydantic import BaseModel, ConfigDict, Field, model_validator

from antgent.clients import openai_aclient
from antgent.utils import import_from_string


class ContextTooLargeError(ValueError): ...


class ModelProvider(BaseModel):
    model_name: str = Field(default="gpt-4o")
    client_name: str = Field(default="openai")
    model_type: Literal["chat", "response"] = Field(default="chat")
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    max_input_tokens: int = Field(default=110000)

    def get_model(self) -> Model:
        if self.client_name == "openai":
            # Only OpenAI uses Reponse API
            return OpenAIResponsesModel(model=self.model_name, openai_client=openai_aclient(self.client_name))
        return OpenAIChatCompletionsModel(model=self.model_name, openai_client=openai_aclient(self.client_name))


MODELS_PROVIDER = {
    "openai": ModelProvider(client_name="openai", model_name="gpt-4o", model_type="response"),
    "gemini": ModelProvider(
        client_name="gemini",
        model_name="gemini-1.5-pro",
        model_type="chat",
        max_input_tokens=900000,
        model_settings=ModelSettings(tool_choice="auto", temperature=0.9, max_tokens=9000, top_p=0.8),
    ),
    "openai-o3": ModelProvider(client_name="openai", model_name="o3-mini", model_type="response"),
}


class AgentModel[TContext](BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow", validate_assignment=True, revalidate_instances="always", arbitrary_types_allowed=True
    )
    name: str = Field(default="AgentBase")
    model_provider: ModelProvider = Field(default_factory=ModelProvider)
    instructions_descr: str = Field(default="")

    instructions_func: str | None = Field(default=None)
    handoffs_import: list[str] = Field(default_factory=list)
    handoff_description: str | None = Field(default=None)
    tools_import: list[str] = Field(default_factory=list)
    output_type_import: str | None = Field(default=None)
    hooks_import: list[str] = Field(default_factory=list)
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    context_type_import: str | None = Field(default=None)
    _context_type: type[Any] | None = None
    _hooks: AgentHooks[Any] | None = None
    _handoffs: list[Agent[Any] | Handoff[Any]] = []
    _tools: list[Tool] = []
    _output_type: type[Any] | None = None
    _instructions: (
        str
        | Callable[
            [RunContextWrapper[TContext], Agent[TContext]],
            MaybeAwaitable[str],
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def import_str(self) -> Self:
        self._instructions = self.instructions_func if self.instructions_func else self.instructions_descr
        self._handoffs = [import_from_string(h) for h in self.handoffs_import]
        self._tools = [import_from_string(t) for t in self.tools_import]
        if self.hooks_import:
            self._hooks = import_from_string(self.hooks_import)
        if self.context_type_import:
            self._context_type = import_from_string(self.context_type_import)
        if self.output_type_import:
            self._output_type = import_from_string(self.output_type_import)
        return self

    def to_agent(self) -> Agent:
        return Agent(
            name=self.name,
            instructions=self._instructions,
            handoffs=self._handoffs,
            model=self.model_provider.get_model(),
            model_settings=self.model_settings,
            tools=self._tools,
            output_type=self._output_type,
            hooks=self._hooks,
        )

    @classmethod
    def from_agent(cls) -> Self:
        raise NotImplementedError


class PrepareRun[TContext](BaseModel):
    input: str | list[TResponseInputItem] = Field(default="")
    context: TContext | None = Field(default=None)
    short_cut: bool = Field(default=False)


TInput = TypeVar("TInput")


class BaseAgent[TInput, TContext]:
    name: str = "Base"
    default_provider: str = "openai"

    def __init__(
        self, model_provider: ModelProvider | str = "gemini", trace_id: str | None = None, span_id: str | None = None
    ) -> None:
        if isinstance(model_provider, str):
            model_provider = MODELS_PROVIDER[model_provider]
        self.model_provider = model_provider
        self.trace_id = trace_id
        self.span_id = span_id

    @abstractmethod
    def agent(self) -> Agent[TContext]: ...

    async def prep_input(self, llm_input: TInput, ctx: TContext) -> PrepareRun[TContext]:
        if not isinstance(llm_input, str) and not isinstance(llm_input, list):
            raise ValueError(f"Input must be a string or list of TResponseInputItem, got {type(llm_input)}")
        return PrepareRun(input=cast(str | list[TResponseInputItem], llm_input), context=ctx, short_cut=False)

    async def prep_response(self, response: RunResult | None, ctx: TContext) -> RunResult | None:
        _ = ctx
        if response is None:
            return None
        return response

    async def run(self, input: TInput, context: TContext, check_tokens: bool = False, **kwargs) -> RunResult | None:
        with custom_span("Prepare input"):
            prep_run = await self.prep_input(input, context)
            if prep_run.short_cut:
                return None
            if (
                check_tokens
                and self.model_provider.max_input_tokens
                and self.count_tokens(prep_run.input) > self.model_provider.max_input_tokens
            ):
                raise ContextTooLargeError(f"Input too large: {self.count_tokens(prep_run.input)} tokens")
        res = await Runner.run(self.agent(), input=prep_run.input, context=prep_run.context, **kwargs)
        return await self.prep_response(res, context)

    def count_tokens(self, content, model="gpt-4o") -> int:
        encoder = tiktoken.encoding_for_model(model)
        return len(encoder.encode(content))

    def truncate(self, content, max_tokens, model="gpt-4o") -> str:
        encoder = tiktoken.encoding_for_model(model)
        return encoder.decode(encoder.encode(content)[0 : max_tokens - 1])
