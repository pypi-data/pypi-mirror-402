"""Setup command group for Runlayer CLI."""

import json
import stat
from datetime import datetime
from enum import Enum
from importlib import resources
from pathlib import Path

import typer

from runlayer_cli.config import resolve_credentials, set_credentials_in_context

app = typer.Typer(help="Setup Runlayer integrations")


class Client(str, Enum):
    """Supported clients for hooks setup."""

    CURSOR = "cursor"


CLIENT_CONFIG_DIRS: dict[Client, Path] = {
    Client.CURSOR: Path.home() / ".cursor",
}


def _get_client_dir(client: Client) -> Path:
    """Get the configuration directory for a client."""
    return CLIENT_CONFIG_DIRS[client]


def _backup_file(file_path: Path) -> Path | None:
    """Create a timestamped backup of a file if it exists.

    Returns the backup path if a backup was created, None otherwise.
    """
    if not file_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = file_path.stem
    suffix = file_path.suffix
    backup_path = file_path.with_name(f"{stem}.backup_{timestamp}{suffix}")
    backup_path.write_bytes(file_path.read_bytes())
    return backup_path


def _read_hook_template() -> str:
    """Read the runlayer-hook.sh template from the package."""
    hook_files = resources.files("hooks")
    return (hook_files / "runlayer-hook.sh").read_text()


def _generate_hooks_json(hook_path: Path) -> dict:
    """Generate the hooks.json configuration for MCP execution hooks only."""
    hook_command = str(hook_path)
    return {
        "version": 1,
        "hooks": {
            "beforeMCPExecution": [{"command": hook_command}],
        },
    }


def _escape_for_double_quotes(value: str) -> str:
    """Escape characters that have special meaning in bash double-quoted strings."""
    # In double quotes, these chars need escaping: $ ` " \ !
    result = value.replace("\\", "\\\\")  # Backslash first
    result = result.replace('"', '\\"')
    result = result.replace("$", "\\$")
    result = result.replace("`", "\\`")
    result = result.replace("!", "\\!")
    return result


def _install_hooks(client: Client, secret: str, host: str) -> None:
    """Install Runlayer hooks for a client."""
    client_dir = _get_client_dir(client)
    hooks_dir = client_dir / "hooks"
    hooks_json_path = client_dir / "hooks.json"
    hook_script_path = hooks_dir / "runlayer-hook.sh"

    hooks_dir.mkdir(parents=True, exist_ok=True)

    hooks_json_backup = _backup_file(hooks_json_path)
    hook_script_backup = _backup_file(hook_script_path)

    if hooks_json_backup:
        typer.echo(f"✓ Backed up existing hooks.json to {hooks_json_backup.name}")
    if hook_script_backup:
        typer.echo(f"✓ Backed up existing hook script to {hook_script_backup.name}")

    hook_template = _read_hook_template()
    hook_content = hook_template.replace(
        "__RUNLAYER_API_KEY__", _escape_for_double_quotes(secret)
    )
    hook_content = hook_content.replace(
        "__RUNLAYER_API_HOST__", _escape_for_double_quotes(host.rstrip("/"))
    )

    hook_script_path.write_text(hook_content)

    current_mode = hook_script_path.stat().st_mode
    hook_script_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    hooks_config = _generate_hooks_json(hook_script_path)
    hooks_json_path.write_text(json.dumps(hooks_config, indent=2) + "\n")

    typer.echo(f"✓ Hooks installed to {client_dir}/")
    typer.echo("✓ Configured hooks: MCP execution validation")
    typer.echo(f"✓ Restart {client.value.title()} to activate")


def _uninstall_hooks(client: Client) -> None:
    """Remove Runlayer hooks from a client."""
    client_dir = _get_client_dir(client)
    hooks_dir = client_dir / "hooks"
    hooks_json_path = client_dir / "hooks.json"
    hook_script_path = hooks_dir / "runlayer-hook.sh"

    removed_anything = False

    if hook_script_path.exists():
        hook_script_path.unlink()
        typer.echo(f"✓ Removed hook script: {hook_script_path}")
        removed_anything = True

    if hooks_json_path.exists():
        hooks_json_path.unlink()
        typer.echo(f"✓ Removed hooks configuration: {hooks_json_path}")
        removed_anything = True

    if removed_anything:
        typer.echo(f"✓ Runlayer hooks removed from {client.value.title()}")
        typer.echo(f"✓ Restart {client.value.title()} to apply changes")
    else:
        typer.echo(f"No Runlayer hooks found for {client.value.title()}")


@app.command(name="hooks", help="Install or uninstall Runlayer client hooks")
def hooks(
    ctx: typer.Context,
    client: Client | None = typer.Option(
        None,
        "--client",
        "-c",
        help="Client to configure (all clients if not specified)",
    ),
    install: bool = typer.Option(False, "--install", "-i", help="Install hooks"),
    uninstall: bool = typer.Option(False, "--uninstall", "-u", help="Uninstall hooks"),
    secret: str | None = typer.Option(
        None,
        "--secret",
        "-s",
        help="API secret for authentication (optional if logged in)",
    ),
    host: str | None = typer.Option(
        None, "--host", "-H", help="Runlayer API host URL (optional if logged in)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Install or uninstall Runlayer hooks for a client.

    Use --install to set up hooks that validate MCP tool calls:
    - Remote MCP servers must be from your Runlayer backend
    - Stdio MCP servers must use the runlayer CLI with valid server UUIDs

    Use --uninstall to remove all Runlayer hooks.

    After any change, restart your client to apply.

    Examples:
        runlayer login --host <url>
        runlayer setup hooks --install
        runlayer setup hooks --client cursor --install --host <url>
        runlayer setup hooks --install --secret <key> --host <url>
        runlayer setup hooks --uninstall
        runlayer setup hooks --client cursor --uninstall --yes
    """
    if install and uninstall:
        typer.echo("Error: Cannot use both --install and --uninstall", err=True)
        raise typer.Exit(1)

    if not install and not uninstall:
        typer.echo("Error: Must specify either --install or --uninstall", err=True)
        raise typer.Exit(1)

    # Determine which clients to process
    clients_to_process = [client] if client else list(Client)

    if install:
        set_credentials_in_context(ctx, secret, host)
        credentials = resolve_credentials(ctx, require_auth=True)
        effective_secret = credentials["secret"]
        effective_host = credentials["host"]

        if not yes:
            if client:
                client_dir = _get_client_dir(client)
                typer.echo(f"This will install Runlayer hooks in {client_dir}/")
            else:
                typer.echo("This will install Runlayer hooks for all clients:")
                for c in clients_to_process:
                    typer.echo(f"  - {_get_client_dir(c)}/")
            typer.echo("  - hooks/runlayer-hook.sh (validates MCP tool calls)")
            typer.echo("  - hooks.json (client hook configuration)")
            typer.echo("")
            if not typer.confirm("Proceed with installation?"):
                typer.echo("Aborted.")
                raise typer.Exit(0)

        for c in clients_to_process:
            _install_hooks(c, effective_secret, effective_host)
    else:
        if not yes:
            if client:
                client_dir = _get_client_dir(client)
                typer.echo(f"This will remove Runlayer hooks from {client_dir}/")
            else:
                typer.echo("This will remove Runlayer hooks from all clients:")
                for c in clients_to_process:
                    typer.echo(f"  - {_get_client_dir(c)}/")
            typer.echo("")
            if not typer.confirm("Proceed with uninstallation?"):
                typer.echo("Aborted.")
                raise typer.Exit(0)

        for c in clients_to_process:
            _uninstall_hooks(c)
