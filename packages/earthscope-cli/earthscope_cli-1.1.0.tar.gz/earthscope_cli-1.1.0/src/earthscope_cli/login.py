from contextlib import suppress
from textwrap import dedent
from typing import TYPE_CHECKING

import typer
from typer_di import Depends, TyperDI

from earthscope_cli.common import get_sdk

with suppress(ModuleNotFoundError):
    from rich import print

if TYPE_CHECKING:
    from earthscope_sdk import EarthScopeClient


app = TyperDI()


@app.command()
def login(sdk=Depends(get_sdk)):
    """
    Log into the EarthScope CLI/SDK.

    Performs the Client Credentials or Device Code flow depending on
    the profile's configuration.
    """
    # lazy import
    from earthscope_sdk.config.models import AuthFlowType

    if sdk.ctx.settings.oauth2.auth_flow_type == AuthFlowType.MachineToMachine:
        _login_client_credentials(sdk)

    else:
        _login_device_code(sdk)

    print(
        f"[green]Successful login! Access token expires at {sdk.ctx.auth_flow.expires_at}"
    )


@app.command()
def logout(sdk=Depends(get_sdk)):
    """
    Log out of the EarthScope CLI/SDK.
    """
    try:
        sdk.ctx.settings.delete_tokens()
    except FileNotFoundError:
        print("Not logged in")
    else:
        print("[green]Logged out")


def _login_client_credentials(sdk: "EarthScopeClient"):
    from earthscope_sdk.auth.error import (
        ClientCredentialsFlowError,
        UnauthorizedError,
    )

    try:
        sdk.ctx.client_credentials_flow.request_tokens()
    except UnauthorizedError:
        print("[red]Unauthorized. Verify client ID and secret")
        raise typer.Exit(1)
    except ClientCredentialsFlowError:
        print("[red]Failed to get access token")
        raise typer.Exit(1)
    except Exception as e:
        print(f"[red]Client Credentials flow failed for unknown reason: {e}")
        raise typer.Exit(1)


def _login_device_code(sdk: "EarthScopeClient"):
    from earthscope_sdk.auth.error import (
        DeviceCodePollingError,
        DeviceCodePollingExpiredError,
        DeviceCodeRequestDeviceCodeError,
        UnauthorizedError,
    )

    # Device Code Flow
    try:
        with sdk.ctx.device_code_flow.do_flow() as codes:
            print(
                dedent(
                    f"""Attempting to automatically open the SSO authorization page in your default browser.
                        If the browser does not open or you wish to use a different device to authorize this request, open the following URL:

                        {codes.verification_uri_complete}"""
                )
            )
            typer.launch(codes.verification_uri_complete)

    except DeviceCodeRequestDeviceCodeError as e:
        print(f"[red]{e}")
        raise typer.Exit(1)

    except UnauthorizedError:
        print("[red]Access denied")
        raise typer.Exit(1)

    except DeviceCodePollingExpiredError:
        print("[red]Authentication session timed out. Restart the authentication")
        raise typer.Exit(1)

    except DeviceCodePollingError as e:
        print(f"[red]Polling failed for unknown reason: {e}")
        raise typer.Exit(1)

    except Exception as e:
        print(f"[red]Device flow failed for unknown reason: {e}")
        raise typer.Exit(1)
