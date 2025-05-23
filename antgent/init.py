#!/usr/bin/env python3
import base64
import os
from typing import Literal

import logfire
import nest_asyncio
from agents import set_trace_processors, set_tracing_export_api_key

from antgent.config import ConfigSchema, LangfuseConfigSchema, LogfireConfigSchema
from antgent.models.agent import LLMConfigSchema
from antgent.utils.aliases import Aliases


def init_envs_langfuse(config: LangfuseConfigSchema):
    # Replace with your Langfuse keys.
    os.environ["LANGFUSE_PUBLIC_KEY"] = os.environ.get("LANGFUSE_PUBLIC_KEY", config.public_key)
    os.environ["LANGFUSE_SECRET_KEY"] = os.environ.get("LANGFUSE_SECRET_KEY", config.secret_key)
    os.environ["LANGFUSE_HOST"] = os.environ.get("LANGFUSE_HOST", config.endpoint)

    # Build Basic Auth header.
    LANGFUSE_AUTH = base64.b64encode(
        f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
    ).decode()

    # Configure OpenTelemetry endpoint & headers
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{os.environ['LANGFUSE_HOST']}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"


def set_env_llm(config: LLMConfigSchema | None, prefix: str | None):
    if not config:
        return
    if not prefix:
        prefix = config.name.upper()
    up = prefix.upper()
    os.environ[f"{up}_API_KEY"] = os.environ.get(f"{up}_API_KEY", config.api_key)
    url = os.environ.get(f"{up}_API_BASE", config.url)
    if url:
        os.environ[f"{up}_API_BASE"] = url


def init_envs_llm(config: ConfigSchema):
    # Replace with your OpenAI keys.
    set_env_llm(config.llms.litellm, "LITELLM_PROXY")
    set_env_llm(config.llms.openai, "OPENAI")
    set_env_llm(config.llms.gemini, "GEMINI")
    if config.llms.litellm_proxy and config.llms.litellm:
        os.environ["LITELLM_USE_PROXY"] = os.environ.get("LITELLM_USE_PROXY", "True")
    for _, conf in config.llms.llms.items():
        set_env_llm(config=conf, prefix=conf.name)
    set_tracing_export_api_key("")


def init_envs(config: ConfigSchema):
    """
    Initialize environment variables
    """
    init_envs_llm(config)


def init_aliases(config: ConfigSchema):
    Aliases.add_aliases(config.aliases.root)


def init_logfire(config: LogfireConfigSchema, mode: Literal["server", "worker"] = "server", extra=None):
    set_trace_processors([])
    if not extra:
        extra = {}

    logfire.configure(token=config.token, environment=extra.get("env", "dev"), send_to_logfire="if-token-present")
    logfire.instrument_openai_agents()
    if mode == "server" and extra is not None and extra.get("app", None):
        app = extra["app"]
        logfire.instrument_fastapi(
            app, capture_headers=True, excluded_urls=[".*/docs", ".*/redoc", ".*/metrics", ".*/health"]
        )


def init(config: ConfigSchema, env: str = "dev", mode: Literal["server", "worker"] = "server", extra=None):
    nest_asyncio.apply()
    if not extra:
        extra = {}
    extra["env"] = env
    init_envs(config)
    if config.traces.enabled:
        init_logfire(config.traces.logfire, mode, extra)
        init_envs_langfuse(config.traces.langfuse)
    else:
        set_trace_processors([])
    init_aliases(config)
