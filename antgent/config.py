# pylint: disable=no-self-argument
import logging
import logging.config
from typing import Any

import ant31box.config
from ant31box.config import BaseConfig, FastAPIConfigSchema, GConfig, LoggingConfigSchema
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from temporalloop.config_loader import TemporalConfigSchema, TemporalScheduleSchema, WorkerConfigSchema

LOGGING_CONFIG: dict[str, Any] = ant31box.config.LOGGING_CONFIG
LOGGING_CONFIG["loggers"].update({"antgent": {"handlers": ["default"], "level": "INFO", "propagate": True}})

logger: logging.Logger = logging.getLogger("antgent")


class LoggingCustomConfigSchema(LoggingConfigSchema):
    log_config: dict[str, Any] | str | None = Field(default_factory=lambda: LOGGING_CONFIG)


class FastAPIConfigCustomSchema(FastAPIConfigSchema):
    server: str = Field(default="antgent.server.server:serve")


class OpenAIProjectKeySchema(BaseConfig):
    api_key: str = Field(default="antgent-openaiKEY")
    project_id: str = Field(default="proj-1xZoR")
    name: str = Field(default="default")
    url: str | None = Field(default=None)


class OpenAIConfigSchema(BaseConfig):
    organization: str = Field(default="Ant31")
    organization_id: str = Field(default="org-1xZoRaUM")
    url: str | None = Field(default=None)
    projects: list[OpenAIProjectKeySchema] = Field(
        default=[
            OpenAIProjectKeySchema(
                api_key="antgent-openaiKEY",
                project_id="proj_OIMUS8HgaQZ",
                name="openai",
            ),
            OpenAIProjectKeySchema(
                api_key="antgent-openaiKEY",
                project_id="proj_NrZHbXS1CDXh",
                name="gemini",
                url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
        ]
    )

    def get_project(self, name: str) -> OpenAIProjectKeySchema | None:
        for project in self.projects:
            if project.name.lower() == name.lower():
                return project
        return None


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
    model_config = SettingsConfigDict(
        env_prefix=f"{ENVPREFIX}_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
    )
    name: str = Field(default="antgent")
    openai: OpenAIConfigSchema = Field(default_factory=OpenAIConfigSchema)
    logging: LoggingConfigSchema = Field(default_factory=LoggingCustomConfigSchema, exclude=True)
    server: FastAPIConfigSchema = Field(default_factory=FastAPIConfigCustomSchema)
    temporalio: TemporalCustomConfigSchema = Field(default_factory=TemporalCustomConfigSchema, exclude=True)
    schedules: dict[str, TemporalScheduleSchema] = Field(default_factory=dict, exclude=True)


class Config(ant31box.config.Config[ConfigSchema]):
    _env_prefix = ENVPREFIX
    __config_class__: type[ConfigSchema] = ConfigSchema

    @property
    def openai(self) -> OpenAIConfigSchema:
        return self.conf.openai

    @property
    def temporalio(self) -> TemporalCustomConfigSchema:
        return self.conf.temporalio

    @property
    def schedules(self) -> dict[str, TemporalScheduleSchema]:
        return self.conf.schedules


def config(path: str | None = None, reload: bool = False) -> Config:
    GConfig[Config].set_conf_class(Config)
    if reload:
        GConfig[Config].reinit()
    # load the configuration
    GConfig[Config](path)
    # Return the instance of the configuration
    return GConfig[Config].instance()
