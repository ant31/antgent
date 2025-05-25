# pylint: disable=no-self-argument
import logging
from typing import Any, Generic, TypeVar

import ant31box.config
from ant31box.config import BaseConfig, FastAPIConfigSchema, GConfig, GenericConfig, LoggingConfigSchema
from pydantic import ConfigDict, Field, RootModel
from pydantic_settings import SettingsConfigDict
from temporalloop.config_loader import TemporalConfigSchema, TemporalScheduleSchema, WorkerConfigSchema

from antgent.models.agent import AgentConfig, AgentsConfigSchema, LLMsConfigSchema
from antgent.utils.aliases import AliasResolver

LOGGING_CONFIG: dict[str, Any] = ant31box.config.LOGGING_CONFIG
LOGGING_CONFIG["loggers"].update({"antgent": {"handlers": ["default"], "level": "INFO", "propagate": True}})

logger: logging.Logger = logging.getLogger("antgent")


class AliasesSchema(RootModel):
    """Schema for managing model aliases."""

    model_config = ConfigDict(validate_assignment=True)
    root: AliasResolver = Field(default_factory=AliasResolver)

    def resolve(self, alias_name: str) -> str:
        return self.root.resolve(alias_name)

    def __setitem__(self, alias: str, value: str):
        self.root.__setitem__(alias, value)

    def __getitem__(self, alias: str) -> str:
        return self.root.__getitem__(alias)

    def __delitem__(self, alias: str):
        self.root.__delitem__(alias)

    def __contains__(self, alias: str) -> bool:
        return self.root.__contains__(alias)

    def __len__(self):
        return self.root.__len__()

    def items(self):
        return self.root.items()

    def values(self):
        return self.root.values()


class LogfireConfigSchema(BaseConfig):
    token: str | None = Field(default=None)
    send_to_logfire: bool | str = Field(default="if-token-present")
    service_name: str = Field(default="")


class LangfuseConfigSchema(BaseConfig):
    public_key: str = Field(default="pk-lf-989f33ac-ad6d-418f-b115-590d7c8b1c95")
    secret_key: str = Field(default="sk-lf-154576f9-d2d2-48c6-84a1-122f03c0a777")
    endpoint: str = Field(default="https://cloud.langfuse.com")


class LoggingCustomConfigSchema(LoggingConfigSchema):
    log_config: dict[str, Any] | str | None = Field(default_factory=lambda: LOGGING_CONFIG)


class TracesConfigSchema(BaseConfig):
    enabled: bool = Field(default=True)
    logfire: LogfireConfigSchema = Field(default_factory=LogfireConfigSchema)
    langfuse: LangfuseConfigSchema = Field(default_factory=LangfuseConfigSchema)


class LiteLLMConfigSchema(BaseConfig):
    base_url: str = Field(default="https://litellm.conny.dev")
    token: str = Field(default="sk-ukiiHpNuHgI2ZqupmPUA4")


class FastAPIConfigCustomSchema(FastAPIConfigSchema):
    server: str = Field(default="antgent.server.server:serve")


class TemporalCustomConfigSchema(TemporalConfigSchema):
    workers: list[WorkerConfigSchema] = Field(
        default=[
            WorkerConfigSchema(
                metric_bind_address="",
                name="antgent-activities",
                queue="antgent-queue-activity",
                activities=[
                    "antgent.temporal.activities:echo",
                ],
                workflows=[],
            ),
            WorkerConfigSchema(
                metric_bind_address="",
                name="antgent-workflow",
                queue="antgent-queue",
                activities=[],
                workflows=[
                    "antgent.temporal.workflows.echo:EchoWorkflow",
                ],
            ),
        ],
    )
    converter: str | None = Field(default="temporalio.contrib.pydantic:pydantic_data_converter")
    # default="temporalloop.converters.pydantic:pydantic_data_converter")


ENVPREFIX = "ANTGENT"


# Main configuration schema
class ConfigSchema(ant31box.config.ConfigSchema):
    _env_prefix = ENVPREFIX

    model_config = SettingsConfigDict(
        env_prefix=f"{ENVPREFIX}_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )
    name: str = Field(default="antgent")
    aliases: AliasesSchema = Field(default_factory=AliasesSchema)
    llms: LLMsConfigSchema = Field(default_factory=LLMsConfigSchema)
    logging: LoggingConfigSchema = Field(default_factory=LoggingCustomConfigSchema, exclude=True)
    temporalio: TemporalCustomConfigSchema = Field(default_factory=TemporalCustomConfigSchema, exclude=True)
    schedules: dict[str, TemporalScheduleSchema] = Field(default_factory=dict, exclude=True)

    agents: AgentsConfigSchema = Field(default_factory=AgentsConfigSchema)
    traces: TracesConfigSchema = Field(default_factory=TracesConfigSchema)


TConfigSchema = TypeVar("TConfigSchema", bound=ConfigSchema)  # pylint: disable= invalid-name


class AntgentConfig(Generic[TConfigSchema], GenericConfig[TConfigSchema]):
    __config_class__: type[TConfigSchema]
    _env_prefix = ENVPREFIX

    @property
    def llms(self) -> LLMsConfigSchema:
        return self.conf.llms

    @property
    def temporalio(self) -> TemporalCustomConfigSchema:
        return self.conf.temporalio

    @property
    def schedules(self) -> dict[str, TemporalScheduleSchema]:
        return self.conf.schedules

    @property
    def traces(self) -> TracesConfigSchema:
        return self.conf.traces

    @property
    def aliases(self) -> AliasResolver:
        return self.conf.aliases.root

    @property
    def agents(self) -> dict[str, AgentConfig]:
        return self.conf.agents.root

    @property
    def agents_schema(self) -> AgentsConfigSchema:
        return self.conf.agents

    @property
    def aliases_schema(self) -> AliasesSchema:
        return self.conf.aliases

    @property
    def logging(self) -> LoggingConfigSchema:
        return self.conf.logging


class Config(AntgentConfig[ConfigSchema]):
    __config_class__: type[ConfigSchema] = ConfigSchema


def config(path: str | None = None, reload: bool = False) -> Config:
    GConfig[Config].set_conf_class(Config)
    if reload:
        GConfig[Config].reinit()
    # load the configuration
    GConfig[Config](path)
    # Return the instance of the configuration
    return GConfig[Config].instance()
