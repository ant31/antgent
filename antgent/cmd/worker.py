from pathlib import Path
from typing import Annotated

import typer
from temporalloop.cmd.looper import main as looper_main
from temporalloop.cmd.scheduler import scheduler as scheduler_main

from antgent.config import config as confload

app = typer.Typer(no_args_is_help=True)


@app.command()
def looper(
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
) -> None:
    """Starts the temporal worker."""
    _ = confload(str(config) if config else None)
    looper_main.main(args=[], standalone_mode=False)


@app.command()
def scheduler(
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
    all: Annotated[bool, typer.Option("--all", help="Run all schedules.")] = False,
    run: Annotated[str | None, typer.Option("--run", help="Run one schedule.")] = None,
    daemon: Annotated[bool, typer.Option("--daemon", help="Run as a daemon.")] = False,
) -> None:
    """Starts the temporal scheduler."""
    _ = confload(str(config) if config else None)
    args = []
    if all:
        args.append("--all")
    if run:
        args.extend(["--run", run])
    if daemon:
        args.append("--daemon")
    scheduler_main.main(args=args, standalone_mode=False)
