from contextlib import suppress

import typer
from typer_di import Depends, TyperDI

from earthscope_cli.common import get_sdk

with suppress(ModuleNotFoundError):
    from rich import print

app = TyperDI()


@app.command(name="get-settings")
def get_settings(
    sdk=Depends(get_sdk),
    plaintext: bool = typer.Option(
        False,
        "--plaintext",
        help="Output secrets in plain text",
    ),
):
    """
    Get SDK settings.
    """

    kwargs = {}
    if plaintext:
        kwargs["context"] = "plaintext"

    output = sdk.ctx.settings.model_dump_json(indent=2, **kwargs)
    print(output)
