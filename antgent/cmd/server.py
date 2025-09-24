#!/usr/bin/env python3
import enum
import logging
from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from antgent.config import config as confload
from antgent.init import init

app = typer.Typer()
logger = logging.getLogger("ant31box.info")


class LogLevel(str, enum.Enum):
    critical = "critical"
    error = "error"
    warning = "warning"
    info = "info"
    debug = "debug"
    trace = "trace"


# pylint: disable=no-value-for-parameter
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
@app.command(context_settings={"auto_envvar_prefix": "FASTAPI"})
def server(  # server_wrapper
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            exists=True,
            help="Configuration file in YAML format.",
            show_default=True,
        ),
    ] = None,
    host: Annotated[str | None, typer.Option("--host", help="Address of the server", show_default=True)] = None,
    port: Annotated[int | None, typer.Option("--port", help="Port to listen on")] = None,
    temporal_host: Annotated[
        str | None, typer.Option("--temporal-host", help="Address of the server", show_default=True)
    ] = None,
    use_colors: Annotated[
        bool,
        typer.Option(
            "--use-colors/--no-use-colors",
            help="Enable/Disable colorized logging.",
        ),
    ] = True,
    log_level: Annotated[
        LogLevel,
        typer.Option(
            "--log-level",
            help="Log level.",
            show_default=True,
            case_sensitive=False,
        ),
    ] = LogLevel.info,
    log_config: Annotated[
        Path | None,
        typer.Option(
            "--log-config",
            exists=True,
            help="Logging configuration file. Supported formats: .ini, .json, .yaml.",
            show_default=True,
        ),
    ] = None,
) -> None:
    _config = confload(str(config) if config else None)
    if host:
        _config.server.host = host
    if port:
        _config.server.port = port
    if temporal_host:
        _config.temporalio.host = temporal_host
    if log_level:
        _config.logging.level = log_level.value
    if log_config:
        _config.logging.log_config = str(log_config)
    if use_colors is not None:
        _config.logging.use_colors = use_colors
    if host:
        _config.conf.server.host = host

    logger.info("Starting server")
    typer.echo(f"{_config.server.model_dump()}")
    init(_config.conf, mode="server")
    uvicorn.run(
        _config.server.server,
        host=_config.server.host,
        port=_config.server.port,
        log_level=_config.logging.level,
        # log_config=config.logging.log_config,
        use_colors=_config.logging.use_colors,
        reload=_config.server.reload,
        factory=True,
    )
