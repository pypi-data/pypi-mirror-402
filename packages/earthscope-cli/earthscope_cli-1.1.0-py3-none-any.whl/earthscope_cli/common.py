from contextlib import suppress
from typing import Annotated, Optional

import typer
from typer_di import Depends

with suppress(ModuleNotFoundError):
    from rich import print

GLOBAL_HELP_PANEL = "Global Options"


def get_sdk(
    ctx: typer.Context,
    profile: Annotated[
        Optional[str],
        typer.Option(
            "--profile",
            "-p",
            help="EarthScope SDK/CLI named profile",
            rich_help_panel=GLOBAL_HELP_PANEL,
        ),
    ] = None,
):
    """
    EarthScopeApiClient dependency (no refresh)
    """
    from earthscope_sdk import EarthScopeClient
    from earthscope_sdk.config.error import ProfileDoesNotExistError
    from earthscope_sdk.config.settings import SdkSettings

    settings_args = {}
    if profile:
        settings_args["profile_name"] = profile

    try:
        settings = SdkSettings(**settings_args)
    except ProfileDoesNotExistError as e:
        print(f"[red]{e.args[0]}")
        raise typer.Exit(1)

    sdk = EarthScopeClient(settings=settings)
    ctx.with_resource(sdk)

    return sdk


def get_sdk_refreshed(
    sdk=Depends(get_sdk),
    auto_refresh: Annotated[
        bool,
        typer.Option(
            "--auto-refresh",
            help="Automatic token refresh. By default the access token is automatically refreshed when nearing or passed expiration.",
            rich_help_panel=GLOBAL_HELP_PANEL,
        ),
    ] = True,
    auto_refresh_threshold: Annotated[
        int,
        typer.Option(
            "--auto-refresh-threshold",
            "-a",
            help="The amount of time remaining (in seconds) before token expiration after which a refresh is automatically attempted.",
            rich_help_panel=GLOBAL_HELP_PANEL,
        ),
    ] = 600,
):
    """
    EarthScopeApiClient dependency (auto refresh)
    """
    if auto_refresh:
        sdk.ctx.auth_flow.refresh_if_necessary(
            auto_refresh_threshold=auto_refresh_threshold
        )

    return sdk
