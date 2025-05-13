from typing import Literal, TypeVar

from agents import (
    TResponseInputItem,
)
from agents.model_settings import ModelSettings
from pydantic import BaseModel, ConfigDict, Field, RootModel

# from agents.guardrails import Guardrail


TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")
type TLLMInput = str | list[TResponseInputItem]


class ModelInfo(BaseModel):
    model: str = Field(default="openai/gpt-4o")
    client: Literal["openai", "gemini", "litellm"] = Field(default="openai")
    api_mode: Literal["chat", "response"] = Field(default="chat")
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    max_input_tokens: int | None = Field(default=None)
    base_url: str | None = Field(default=None)
    api_key: str | None = Field(default=None)


class AgentConfig(ModelInfo):
    name: str = Field(default="", description="name the agent")
    description: str = Field(default="", description="Description of the agent")


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
