"""Configuration management for Runlayer CLI.

This module handles loading and saving CLI configuration to ~/.runlayer/config.yaml.
The config file stores authentication credentials obtained via the login command.

Config structure:
    default_host: https://app.runlayer.com
    hosts:
      app.runlayer.com:
        url: https://app.runlayer.com
        secret: api_key_here
      localhost:8000:
        url: http://localhost:8000
        secret: local_api_key
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TypedDict
from urllib.parse import urlparse

import typer
import yaml

from runlayer_cli.paths import get_runlayer_dir


class HostConfig(TypedDict, total=False):
    """Configuration for a single host."""

    url: str
    secret: str


class ConfigData(TypedDict, total=False):
    """Configuration data structure."""

    default_host: str
    hosts: dict[str, HostConfig]


def url_to_host_key(url: str) -> str:
    """Convert URL to config key (hostname:port or just hostname).

    Args:
        url: Full URL including scheme (e.g., https://app.runlayer.com)

    Returns:
        Config key in format hostname or hostname:port
        Port is omitted if it's the default for the scheme (80 for http, 443 for https)
    """
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port

    # Omit port if it's the default for the scheme
    if port and not (
        (parsed.scheme == "https" and port == 443)
        or (parsed.scheme == "http" and port == 80)
    ):
        return f"{host}:{port}"
    return host


def normalize_url(url: str) -> str:
    """Normalize a URL by stripping trailing slashes.

    Args:
        url: URL to normalize

    Returns:
        URL with trailing slashes removed
    """
    return url.rstrip("/")


@dataclass
class Config:
    """CLI configuration with per-host credentials."""

    default_host: Optional[str] = None
    hosts: dict[str, HostConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: ConfigData) -> "Config":
        """Create Config from dictionary."""
        return cls(
            default_host=data.get("default_host"),
            hosts=data.get("hosts", {}),
        )

    def to_dict(self) -> ConfigData:
        """Convert to dictionary for serialization."""
        result: ConfigData = {}
        if self.default_host:
            result["default_host"] = self.default_host
        if self.hosts:
            result["hosts"] = self.hosts
        return result

    def get_secret_for_host(self, url: str) -> Optional[str]:
        """Get the secret for a specific host URL.

        Args:
            url: Full URL including scheme (e.g., https://app.runlayer.com)

        Returns:
            The secret if found and URL matches exactly, None otherwise
        """
        url = normalize_url(url)
        key = url_to_host_key(url)
        host_config = self.hosts.get(key)

        if not host_config:
            return None

        # Verify the stored URL matches exactly (scheme matters!)
        stored_url = normalize_url(host_config.get("url", ""))
        if stored_url != url:
            return None

        return host_config.get("secret")

    def set_host_credentials(self, url: str, secret: str) -> None:
        """Set credentials for a specific host.

        Also updates default_host to this URL.

        Args:
            url: Full URL including scheme
            secret: API secret/key for this host
        """
        url = normalize_url(url)
        key = url_to_host_key(url)

        self.hosts[key] = HostConfig(url=url, secret=secret)
        self.default_host = url

    def clear_host(self, url: str) -> bool:
        """Clear credentials for a specific host.

        Args:
            url: Full URL including scheme

        Returns:
            True if host was found and cleared, False otherwise
        """
        url = normalize_url(url)
        key = url_to_host_key(url)

        host_config = self.hosts.get(key)
        if not host_config:
            return False

        # Verify the stored URL matches exactly (scheme matters!)
        stored_url = normalize_url(host_config.get("url", ""))
        if stored_url != url:
            return False

        del self.hosts[key]
        # If this was the default host, clear it
        if self.default_host and normalize_url(self.default_host) == url:
            self.default_host = None
        return True

    # Backwards compatibility properties
    @property
    def host(self) -> Optional[str]:
        """Get the default host URL."""
        return self.default_host

    @property
    def secret(self) -> Optional[str]:
        """Get the secret for the default host."""
        if not self.default_host:
            return None
        return self.get_secret_for_host(self.default_host)


def get_config_path() -> Path:
    """Get the path to the config file.

    Returns:
        Path to ~/.runlayer/config.yaml
    """
    return get_runlayer_dir() / "config.yaml"


def load_config() -> Config:
    """Load configuration from the config file.

    Returns:
        Config object with loaded values, or empty Config if file doesn't exist
    """
    config_path = get_config_path()

    if not config_path.exists():
        return Config()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return Config()
            return Config.from_dict(data)
    except (yaml.YAMLError, OSError) as e:
        typer.secho(
            f"Warning: Could not parse config file at {config_path}: {e}. "
            "Using default configuration.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        return Config()


def save_config(config: Config) -> None:
    """Save configuration to the config file.

    Creates the config directory if it doesn't exist.
    Sets file permissions to 0600 (user read/write only) for security.

    Args:
        config: Config object to save
    """
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config.to_dict(), f, default_flow_style=False)

    try:
        os.chmod(config_path, 0o600)
    except OSError:
        pass


def clear_config() -> None:
    """Clear the configuration file.

    Removes the config file if it exists.
    """
    config_path = get_config_path()

    if config_path.exists():
        config_path.unlink()


class ResolvedCredentials(TypedDict):
    """Resolved credentials for API authentication."""

    secret: str
    host: str


def set_credentials_in_context(
    ctx: typer.Context,
    secret: Optional[str],
    host: Optional[str],
) -> None:
    """Store CLI-provided credentials in typer context for resolve_credentials.

    This exists for backwards compatibility: commands previously required --secret
    and --host as direct options. Now they can also be provided via global options
    or config file, but we still accept them at the command level.

    Args:
        ctx: Typer context to store credentials in
        secret: API secret from command-level --secret option
        host: Host URL from command-level --host option
    """
    ctx.ensure_object(dict)
    if secret:
        ctx.obj["secret"] = secret
    if host:
        ctx.obj["host"] = host


def resolve_credentials(
    ctx: typer.Context,
    require_auth: bool = True,
) -> ResolvedCredentials:
    """Resolve credentials from CLI args, config file, or trigger login flow.

    Resolution order:
    1. CLI args (from ctx.obj, set by global --secret/--host options)
    2. Config file (~/.runlayer/config.yaml) - credentials are looked up by host

    Security: A secret is only used if it was explicitly stored for that exact
    host URL (including scheme). This prevents credential leakage when --host
    differs from the configured host.

    Args:
        ctx: Typer context containing CLI args in ctx.obj
        require_auth: If True, trigger login when credentials are missing

    Returns:
        Dict with 'secret' and 'host' keys

    Raises:
        typer.Exit: If host is not provided via CLI or config file
        typer.Exit: If require_auth=True and authentication fails or is cancelled
    """
    cli_secret: Optional[str] = None
    cli_host: Optional[str] = None

    # Walk up context chain for nested subcommands (main -> deploy -> validate)
    current_ctx = ctx
    while current_ctx:
        if current_ctx.obj:
            if cli_secret is None:
                cli_secret = current_ctx.obj.get("secret")
            if cli_host is None:
                cli_host = current_ctx.obj.get("host")
        current_ctx = current_ctx.parent  # type: ignore[assignment]

    config = load_config()

    # Determine effective host
    effective_host = cli_host or config.default_host
    if not effective_host:
        typer.secho(
            "Error: No host configured. "
            "Please provide --host or run 'runlayer login --host <url>' first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    effective_host = normalize_url(effective_host)

    # Determine effective secret
    # Priority: CLI secret > config secret for this specific host
    if cli_secret:
        effective_secret = cli_secret
    else:
        # Look up secret for this specific host (security: no cross-host leakage)
        effective_secret = config.get_secret_for_host(effective_host)

    if effective_secret:
        return {"secret": effective_secret, "host": effective_host}

    if not require_auth:
        return {"secret": "", "host": effective_host}

    typer.secho(
        "No credentials found for this host. Starting login flow...",
        fg=typer.colors.YELLOW,
        err=True,
    )

    from runlayer_cli.commands.auth import login  # avoid circular import

    login(host=effective_host)

    config = load_config()

    # After login, get the secret for this host
    secret_after_login = config.get_secret_for_host(effective_host)
    if not secret_after_login:
        typer.secho(
            "Error: Authentication failed. Please try again with 'runlayer login'.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    return {"secret": secret_after_login, "host": effective_host}
