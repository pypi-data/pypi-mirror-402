from contextlib import suppress

import typer
from typer_di import Depends, TyperDI

from earthscope_cli import login
from earthscope_cli.common import get_sdk, get_sdk_refreshed

with suppress(ModuleNotFoundError):
    from rich import print

app = TyperDI()

# Register aliases to login/logout
app.add_typer(login.app)


@app.command(name="get-access-token")
def get_access_token(sdk=Depends(get_sdk_refreshed)):
    """
    Get the access token.

    Automatically refreshes the token when necessary.
    """
    typer.echo(sdk.ctx.auth_flow.access_token)


@app.command(name="get-access-token-body")
def get_access_token_body(sdk=Depends(get_sdk_refreshed)):
    """
    Get the access token's body.

    Automatically refreshes the token when necessary.
    """
    body = sdk.ctx.auth_flow.access_token_body.model_dump_json(
        by_alias=True,
        indent=2,
        exclude_none=True,
    )
    print(body)


@app.command(name="get-aws-credentials")
def get_aws_credentials(
    sdk=Depends(get_sdk_refreshed),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force AWS credentials refresh. By default, AWS creds are only refreshed when near expiration.",
    ),
    role: str = typer.Argument(
        "s3-miniseed",
        help="The AWS role to use for credentials.",
    ),
):
    """
    Get temporary AWS credentials to directly access EarthScope's
    AWS resources (e.g. S3 buckets).
    """
    creds = sdk.user.get_aws_credentials(role=role, force=force)
    print(creds.model_dump_json(indent=2))


@app.command(name="get-profile")
def get_profile(sdk=Depends(get_sdk_refreshed)):
    """
    Get the user profile associated with these credentials.
    """
    profile = sdk.user.get_profile()
    body = profile.model_dump_json(
        by_alias=True,
        indent=2,
        exclude_none=True,
    )
    print(body)


@app.command(name="get-refresh-token")
def get_refresh_token(sdk=Depends(get_sdk)):
    """
    Get the refresh token.
    """
    typer.echo(sdk.ctx.auth_flow.refresh_token)


@app.command(name="refresh-access-token")
def refresh_access_token(sdk=Depends(get_sdk)):
    """
    Refresh the access token immediately.

    Most commands in the CLI will transparently manage token refresh for you.
    """
    sdk.ctx.auth_flow.refresh()
    print(
        f"[green]Successful refresh! New access token expires at {sdk.ctx.auth_flow.expires_at})"
    )


@app.command(name="revoke-refresh-token")
def revoke_refresh_token(sdk=Depends(get_sdk)):
    """
    Revoke the refresh token immediately.

    This invalidates the refresh token server-side so it can never again be used to
    get new access tokens. This would be useful if you think your refresh token has
    been compromised.

    You will need to log in again after revoking your refresh token.
    """
    sdk.ctx.auth_flow.revoke_refresh_token()
    sdk.ctx.settings.delete_tokens(missing_ok=True)
    print(
        "[green]Refresh token successfully revoked. Please re-authenticate to start a new refreshable session."
    )
