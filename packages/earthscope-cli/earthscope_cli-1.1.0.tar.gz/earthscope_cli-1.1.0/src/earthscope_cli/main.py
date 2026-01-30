from contextlib import suppress
from typing import Annotated

import typer
from earthscope_sdk import __version__ as sdk_version
from earthscope_sdk.auth.error import (
    InvalidRefreshTokenError,
    NoAccessTokenError,
    NoRefreshTokenError,
    NoTokensError,
    UnauthorizedError,
)

from earthscope_cli import __version__ as cli_version
from earthscope_cli import debug, login, user
from earthscope_cli.dropoff.typer import app as dropoff_app
from earthscope_cli.util import ErrorHandlingTyper

with suppress(ModuleNotFoundError):
    from rich import print

app = ErrorHandlingTyper(
    pretty_exceptions_enable=False,
)


@app.error_handler(
    InvalidRefreshTokenError,
    NoAccessTokenError,
    NoRefreshTokenError,
    NoTokensError,
    UnauthorizedError,
)
def translate_error(exc):
    if isinstance(exc, InvalidRefreshTokenError):
        print(
            "[red]Unable to refresh because the refresh token is not valid. To resolve, re-authenticate."
        )

    elif isinstance(exc, NoTokensError):
        print("[red]No tokens found for profile. To resolve, re-authenticate.")

    elif isinstance(exc, UnauthorizedError):
        print("[red]You are not authorized to perform this action.")

    return 1


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Print the CLI and SDK versions",
        ),
    ] = False,
):
    """
    The EarthScope CLI can be used to interact with EarthScope's APIs.
    """
    if ctx.invoked_subcommand:
        return

    if version:
        typer.echo(f"earthscope-cli/{cli_version} earthscope-sdk/{sdk_version}")
        raise typer.Exit()

    print(ctx.get_help())


# Add login/logout functionality as top-level commands
app.add_typer(login.app)

app.add_typer(
    dropoff_app,
    name="dropoff",
    help="Use the EarthScope Dropoff system",
    no_args_is_help=True,
)

app.add_typer(
    user.app,
    name="user",
    help="Use Earthscope API user endpoints",
    no_args_is_help=True,
)

app.add_typer(
    debug.app,
    name="debug",
    help="Debugging commands",
    no_args_is_help=True,
    hidden=True,
)


if __name__ == "__main__":
    app()
