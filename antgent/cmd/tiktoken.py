import json
from typing import Annotated

import tiktoken
from ant31box.cmd.typer.models import OutputEnum
from typer import Exit, Option, echo, get_text_stream


def tikcount(
    output: Annotated[
        OutputEnum,
        Option("--output", "-o", help="Output format."),
    ] = OutputEnum.json,
) -> None:
    """Counts tokens from stdin."""
    stdin_text = get_text_stream("stdin")
    model = "gpt-4o"
    encoder = tiktoken.encoding_for_model(model)
    res = {"tokens": len(encoder.encode(stdin_text.read())), "model": model}
    if output == "json":
        echo(json.dumps(res, indent=2))
    else:
        echo(res["tokens"])
    raise Exit()
