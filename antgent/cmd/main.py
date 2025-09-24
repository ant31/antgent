#!/usr/bin/env python3
import typer
from ant31box.cmd.typer.default_config import app as default_config_app
from ant31box.cmd.typer.version import app as version_app

from antgent.config import config
from antgent.version import VERSION

from .server import app as server_app
from .tiktoken import tikcount
from .worker import app as worker_app

app = typer.Typer(no_args_is_help=True)


def main() -> None:
    # "init config"
    _ = config()
    _ = VERSION.app_version

    # Start the Temporalio Worker
    app.add_typer(worker_app)

    # Add other commands
    app.add_typer(version_app)
    app.add_typer(server_app)
    app.add_typer(default_config_app)
    app.command()(tikcount)

    # Parse cmd-line arguments and options
    # pylint: disable=no-value-for-parameter
    app()


if __name__ == "__main__":
    main()
