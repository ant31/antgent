from typing import Any, Literal, TypeVar

from agents import (
    TResponseInputItem,
)
from agents.model_settings import ModelSettings
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, RootModel

from .visibility import Visibility

# from agents.guardrails import Guardrail


TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
type TLLMInput = str | list[TResponseInputItem]


class ModelInfo(BaseModel):
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    model: str = Field(default="openai/gpt-4o")
    client: Literal["openai", "gemini", "litellm"] = Field(default="openai")
    api_mode: Literal["chat", "response"] = Field(default="chat")
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    max_input_tokens: int | None = Field(default=None)
    base_url: str | None = Field(default=None)
    api_key: str | None = Field(default=None)


class AgentConfig(ModelInfo):
    model_config = ConfigDict(extra="allow", validate_assignment=True)
    name: str = Field(default="", description="name the agent")
    description: str = Field(default="", description="Description of the agent")


TOutput = TypeVar("TOutput")
TStructured = TypeVar("TStructured")


class AgentFrozenConfig[TOutput, TStructured](BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    output_cls: type[TOutput] | None = Field(default=None, description="The output class of the agent")
    structured: bool = Field(default=True, description="If True, the agent will return a structured output")
    structured_cls: type[TStructured] | None = Field(
        default=None, description="The structured output class of the agent"
    )

    def get_structured_cls(self) -> type[TStructured] | None:
        if self.structured and self.structured_cls is None and self.output_cls is None:
            raise ValueError("If structured is True, structured_cls or output_cls must be provided")
        if self.structured and self.structured_cls is None and self.output_cls is not None:
            # If structured is True but structured_cls is None, use output_cls as structured_cls
            return self.output_cls
        return self.structured_cls


class AgentsConfigSchema(RootModel):
    root: dict[str, AgentConfig] = Field(default_factory=dict)

    def get(self, name: str) -> AgentConfig | None:
        if name in self.root:
            return self.root[name]
        return None


class PrepareRun[TContext](BaseModel):
    llm_input: TLLMInput = Field(default="")
    context: TContext | None = Field(default=None)
    short_cut: bool = Field(default=False)


class AgentRunMetadata(BaseModel):
    trace_id: str | None = Field(default=None)
    span_id: str | None = Field(default=None)
    session_id: str | None = Field(default=None)
    parent_name: str | None = Field(default=None)


class LLMConfigSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    api_key: str = Field(default="antgent-openaiKEY")
    project_id: str = Field(default="proj-1xZoR")
    organization_id: str = Field(default="org-1xZoRaUM")
    name: str = Field(default="default")
    url: str | None = Field(default=None)


class LLMsConfigSchema(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    litellm_proxy: bool = Field(default=False)
    openai: LLMConfigSchema | None = Field(default=None)
    litellm: LLMConfigSchema | None = Field(default=None)
    gemini: LLMConfigSchema | None = Field(default=None)
    llms: dict[str, LLMConfigSchema] = Field(default_factory=dict)

    def get_project(self, name: str) -> LLMConfigSchema | None:
        if hasattr(self, name) and getattr(self, name) is not None:
            return getattr(self, name)
        return self.llms.get(name, None)


class WorkflowInfo(BaseModel):
    name: str = Field(default="", description="The name of the agent workflow to run")
    wid: str = Field(default="", description="The ID of the agent workflow to run")
    run_id: str = Field(default="", description="The ID of the agent workflow run")
    namespace: str = Field(default="", description="The namespace of the agent workflow run")


class AgentRunCost(BaseModel):
    total_tokens: int = Field(default=0, description="The total number of tokens used in the agent workflow run")
    total_time: float = Field(default=0.0, description="The total time taken for the agent workflow run")
    total_cost: float = Field(default=0.0, description="The total cost of the agent workflow run")


class AgentWorkflowOutput[WOutput](BaseModel):
    model_config = ConfigDict(extra="allow")
    result: WOutput | None = Field(..., description="The output data from the agent workflow")
    metadata: dict[str, Any] = Field(default_factory=dict, description="The metadata for the agent workflow run")
    cost: AgentRunCost | None = Field(default=None, description="The cost of the agent workflow run")
    workflow_info: WorkflowInfo | None = Field(default=None, description="The information about the agent workflow run")
    visibility: Visibility = Field(
        default_factory=Visibility, description="The visibility information for the agent workflow run"
    )


class AgentWorkflowInput[TInput](BaseModel):
    context: TInput = Field(..., description="The input data for the agent workflow")
    llm_input: str = Field(
        default="",
        description="The input data for the agent workflow",
        validation_alias=AliasChoices("llm_input", "input"),
    )
    visibility: Visibility = Field(
        default_factory=Visibility, description="The visibility information for the agent workflow run"
    )
    wid: WorkflowInfo = Field(default_factory=WorkflowInfo, description="The ID of the temporal workflow")


from antgent.agents.summarizer.models import SummaryInput, SummaryResult  # noqa: E402


class AgentTextSummaryWorkflowOutput(AgentWorkflowOutput[SummaryResult]): ...


class AgentTextSummaryWorkflowInput(AgentWorkflowInput[SummaryInput]): ...
