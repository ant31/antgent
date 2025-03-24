import json

import click
import tiktoken


@click.command()
@click.option("--output", "-o", default="json", type=click.Choice(["json", "text"]))
@click.pass_context
def tikcount(
    ctx: click.Context,
    output: str,
) -> None:
    stdin_text = click.get_text_stream("stdin")
    model = "gpt-4o"
    encoder = tiktoken.encoding_for_model(model)
    res = {"tokens": len(encoder.encode(stdin_text.read())), "model": model}
    if output == "json":
        click.echo(json.dumps(res, indent=2))
    else:
        click.echo(res["tokens"])
    ctx.exit()
