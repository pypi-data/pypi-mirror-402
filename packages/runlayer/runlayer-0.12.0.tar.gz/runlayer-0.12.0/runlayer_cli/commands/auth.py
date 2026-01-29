"""CLI authentication commands using WorkOS Device Authorization Flow."""

import time
import webbrowser
from typing import Optional

import httpx
import typer

from runlayer_cli.api import USER_AGENT
from runlayer_cli.config import clear_config, load_config, normalize_url, save_config


def login(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-H",
        help="Runlayer host URL (required if not in config)",
    ),
) -> None:
    """Authenticate with Runlayer using browser-based device flow.

    Displays a code in the terminal and opens a browser for authentication.
    After login, credentials are saved to ~/.runlayer/config.yaml for this host.
    """
    config = load_config()
    effective_host = host or config.default_host

    if not effective_host:
        typer.secho(
            "Error: No host configured. Please provide --host <url>.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    effective_host = normalize_url(effective_host)

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{effective_host}/api/v1/cli/device/authorize",
                headers={"User-Agent": USER_AGENT},
            )

            if response.status_code != 200:
                typer.secho(
                    f"Failed to initiate authentication: {response.text}",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(1)

            data = response.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_uri = data["verification_uri"]
            verification_uri_complete = data["verification_uri_complete"]
            expires_in = data["expires_in"]
            interval = data["interval"]

            typer.echo("", err=True)
            typer.secho("  To authenticate, visit:", fg=typer.colors.WHITE, err=True)
            typer.secho(
                f"  {verification_uri}", fg=typer.colors.CYAN, bold=True, err=True
            )
            typer.echo("", err=True)
            typer.secho("  And enter code:", fg=typer.colors.WHITE, err=True)
            typer.secho(f"  {user_code}", fg=typer.colors.GREEN, bold=True, err=True)
            typer.echo("", err=True)

            typer.echo("Opening browser...", err=True)
            webbrowser.open(verification_uri_complete)

            typer.echo("Waiting for authentication...", err=True)

            start_time = time.time()
            poll_interval = interval

            while time.time() - start_time < expires_in:
                time.sleep(poll_interval)

                try:
                    token_response = client.post(
                        f"{effective_host}/api/v1/cli/device/token",
                        json={"device_code": device_code},
                        headers={"User-Agent": USER_AGENT},
                    )

                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        api_key = token_data["api_key"]

                        # Save credentials for this specific host
                        config.set_host_credentials(effective_host, api_key)
                        save_config(config)

                        typer.echo("", err=True)
                        typer.secho(
                            "Successfully authenticated!",
                            fg=typer.colors.GREEN,
                            bold=True,
                            err=True,
                        )
                        typer.echo(
                            "Credentials saved to ~/.runlayer/config.yaml",
                            err=True,
                        )
                        typer.echo(f"Host: {effective_host}", err=True)
                        return

                    elif token_response.status_code == 202:
                        detail = token_response.json().get("detail", "")
                        if detail == "slow_down":
                            poll_interval += 1
                        continue

                    else:
                        error_detail = token_response.json().get(
                            "detail", "Authentication failed"
                        )
                        typer.secho(
                            f"Authentication failed: {error_detail}",
                            fg=typer.colors.RED,
                            err=True,
                        )
                        raise typer.Exit(1)

                except httpx.RequestError as e:
                    typer.secho(
                        f"Network error during polling: {e}",
                        fg=typer.colors.RED,
                        err=True,
                    )
                    raise typer.Exit(1)

            typer.secho(
                "Authentication timed out. Please try again.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1)

    except httpx.RequestError as e:
        typer.secho(
            f"Failed to connect to {effective_host}: {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    except KeyboardInterrupt:
        typer.echo("\nAuthentication cancelled.", err=True)
        raise typer.Exit(1)


def logout(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        "-H",
        help="Clear credentials for specific host only. If not provided, clears all credentials.",
    ),
) -> None:
    """Clear saved Runlayer credentials from ~/.runlayer/config.yaml.

    By default, clears all credentials. Use --host to clear credentials for a specific host only.
    """
    config = load_config()

    if not config.hosts:
        typer.echo("No credentials found.", err=True)
        return

    if host:
        # Clear credentials for specific host only
        host = normalize_url(host)
        if config.clear_host(host):
            save_config(config)
            typer.secho(
                f"Credentials cleared for {host}.", fg=typer.colors.GREEN, err=True
            )
        else:
            typer.echo(f"No credentials found for {host}.", err=True)
    else:
        # Clear all credentials
        clear_config()
        typer.secho(
            "All credentials cleared successfully.", fg=typer.colors.GREEN, err=True
        )
