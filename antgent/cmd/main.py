#!/usr/bin/env python3
import click
from ant31box.cmd.default_config import default_config
from ant31box.cmd.version import version
from temporalloop.cmd.looper import main as looper_main
from temporalloop.cmd.scheduler import scheduler

from antgent.config import config
from antgent.version import VERSION

from .server import server
from .tiktoken import tikcount


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    ctx.ensure_object(dict)


def main() -> None:
    # "init config"
    _ = config()
    _ = VERSION.app_version

    # Start the Temporalio Worker
    cli.add_command(scheduler)
    cli.add_command(looper_main, name="looper")
    cli.add_command(tikcount)
    # Display version
    cli.add_command(version)
    cli.add_command(server)
    # Show default config
    cli.add_command(default_config)
    # Parse cmd-line arguments and options
    # pylint: disable=no-value-for-parameter
    cli()


if __name__ == "__main__":
    main()
