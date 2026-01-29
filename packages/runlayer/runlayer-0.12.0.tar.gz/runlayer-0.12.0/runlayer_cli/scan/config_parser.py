"""Parse MCP client configuration files."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import json5
import structlog
import yaml

if TYPE_CHECKING:
    from runlayer_cli.scan.clients import MCPClientDefinition

logger = structlog.get_logger(__name__)


@dataclass
class MCPServerConfig:
    """Parsed MCP server configuration."""

    name: str
    type: str  # stdio, sse, http, streaming-http
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    config_hash: str = ""
    project_name: str | list[str] | None = None


@dataclass
class MCPClientConfig:
    """Parsed MCP client configuration."""

    client: str
    client_version: str | None = None
    config_path: str | None = None
    config_modified_at: str | None = None
    servers: list[MCPServerConfig] = field(default_factory=list)
    # New fields for global vs project-level configs
    config_scope: str = "global"  # "global" or "project"
    project_path: str | None = (
        None  # Path to project root (only for project-level configs)
    )


def compute_config_hash(server: MCPServerConfig) -> str:
    """
    Compute a canonical hash for a server configuration.

    Hash includes: name, type, command, args, url
    Hash excludes: env, headers (credentials can vary)

    Args order is preserved because argument order is semantically meaningful.
    """
    canonical = {
        "name": server.name,
        "type": server.type,
        "command": server.command,
        "args": list(server.args) if server.args else [],
        "url": server.url,
    }
    canonical_json = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(canonical_json.encode()).hexdigest()


def _parse_goose_extension(name: str, config: dict[str, Any]) -> MCPServerConfig | None:
    """Parse a Goose extension entry from config file.

    Goose uses a different config format:
    - Uses 'cmd' instead of 'command'
    - Uses 'envs' instead of 'env'
    - Uses 'uri' instead of 'url'
    - Has 'enabled' flag (only parse if enabled=True)
    - Has 'type' field - only parse MCP transport types ('stdio', 'sse',
      'streamable_http'), skip internal types ('platform', 'builtin')

    Args:
        name: Extension name (key in extensions dict)
        config: Extension configuration dictionary

    Returns:
        MCPServerConfig if extension is valid and enabled, None otherwise
    """
    # Check if extension is enabled
    if not config.get("enabled", False):
        return None

    # Only process MCP transport types (skip platform, builtin, etc.)
    ext_type = config.get("type", "")
    valid_transport_types = ("stdio", "sse", "streamable_http")
    if ext_type not in valid_transport_types:
        return None

    # Use display_name or name field if available, otherwise use the key
    display_name = config.get("name", name)

    # Map Goose field names to standard MCP format
    envs = config.get("envs")

    if ext_type == "stdio":
        # stdio type uses cmd/args
        command = config.get("cmd")
        args = config.get("args")
        server = MCPServerConfig(
            name=display_name,
            type="stdio",
            command=command,
            args=args,
            url=None,
            env=envs if envs else None,
            headers=None,
            project_name=config.get("project_name"),
        )
    else:
        # sse, streamable_http types use uri (Goose uses 'uri' not 'url')
        url = config.get("uri")
        headers = config.get("headers")
        # Normalize type name (streamable_http -> streamable-http for consistency)
        normalized_type = ext_type.replace("_", "-")
        server = MCPServerConfig(
            name=display_name,
            type=normalized_type,
            command=None,
            args=None,
            url=url,
            env=envs if envs else None,
            headers=headers,
            project_name=config.get("project_name"),
        )

    server.config_hash = compute_config_hash(server)
    return server


def _parse_zed_context_server(
    name: str, config: dict[str, Any]
) -> MCPServerConfig | None:
    """Parse a Zed context_servers entry.

    Zed format:
    - 'enabled': bool (skip if false, defaults to true)
    - 'command': string, 'args': list, 'env': dict (stdio transport)
    - 'url': string, 'headers': dict (remote/SSE transport)
    - 'settings': dict (extension settings - skip entries with only settings)

    Args:
        name: Server name (key in context_servers dict)
        config: Server configuration dictionary

    Returns:
        MCPServerConfig if server is valid and enabled, None otherwise
    """
    # Skip disabled servers (defaults to enabled if not specified)
    if not config.get("enabled", True):
        return None

    # Determine transport type based on config
    if "url" in config:
        # Remote/SSE server
        server = MCPServerConfig(
            name=name,
            type="sse",
            command=None,
            args=None,
            url=config.get("url"),
            env=config.get("env"),
            headers=config.get("headers"),
            project_name=config.get("project_name"),
        )
    elif "command" in config:
        # stdio server with command
        server = MCPServerConfig(
            name=name,
            type="stdio",
            command=config.get("command"),
            args=config.get("args"),
            url=None,
            env=config.get("env"),
            headers=None,
            project_name=config.get("project_name"),
        )
    else:
        # Extension-only entry (has 'settings' but no command/url)
        # These are placeholders for extensions - skip them
        return None

    server.config_hash = compute_config_hash(server)
    return server


def _parse_server_entry(name: str, config: dict[str, Any]) -> MCPServerConfig:
    """Parse a single server entry from config file.

    Handles two formats:
    1. Standard MCP format: { "command": "...", "args": [...], "env": {...} }
    2. Claude Desktop extensions format:
       {
         "manifest": {
           "display_name": "...",
           "server": {
             "type": "node",
             "entry_point": "server/index.js",
             "mcp_config": { "command": "node", "args": [...], "env": {...} }
           }
         }
       }
    """
    # Check if this is Claude Desktop extensions format
    if "manifest" in config:
        manifest = config["manifest"]
        # Use display_name as the server name if available
        display_name = manifest.get("display_name", name)
        server_info = manifest.get("server", {})

        # Check for mcp_config which contains standard format
        mcp_config = server_info.get("mcp_config", {})
        if mcp_config:
            # Use mcp_config which has standard command/args
            command = mcp_config.get("command")
            args = mcp_config.get("args")
            env = mcp_config.get("env")
        else:
            # Fallback: parse entry_point if no mcp_config
            entry_point = server_info.get("entry_point", "")
            command = None
            args = None
            env = None

            if entry_point:
                parts = entry_point.split()
                if parts:
                    command = parts[0]
                    args = parts[1:] if len(parts) > 1 else []

        # Map server type (node -> stdio for MCP purposes)
        server_type = server_info.get("type", "stdio")
        if server_type == "node":
            server_type = "stdio"

        server = MCPServerConfig(
            name=display_name,
            type=server_type,
            command=command,
            args=args,
            url=None,
            env=env,
            headers=None,
            project_name=config.get("project_name"),
        )
    else:
        # Standard MCP format
        # Determine transport type
        if "url" in config:
            transport_type = config.get("transport", "sse")
        else:
            transport_type = "stdio"

        server = MCPServerConfig(
            name=name,
            type=transport_type,
            command=config.get("command"),
            args=config.get("args"),
            url=config.get("url"),
            env=config.get("env"),
            headers=config.get("headers"),
            project_name=config.get("project_name"),
        )

    server.config_hash = compute_config_hash(server)
    return server


def parse_config_file(
    client_def: MCPClientDefinition,
    config_path: Path,
) -> MCPClientConfig | None:
    """
    Parse an MCP client configuration file.

    Uses the client definition to determine how to extract servers from the
    config file, handling client-specific JSON/YAML structures.

    Args:
        client_def: Client definition with parsing configuration
        config_path: Path to the configuration file

    Returns:
        MCPClientConfig if successfully parsed, None if file doesn't exist or is invalid
    """
    if not config_path.exists():
        logger.debug(
            "Config file not found",
            client=client_def.name,
        )
        return None

    # Determine config format from client definition
    config_format = getattr(client_def, "config_format", "json")

    try:
        with open(config_path, encoding="utf-8") as f:
            if config_format == "yaml":
                raw_config = yaml.safe_load(f)
            else:
                # Use json5 for JSONC support (handles comments, trailing commas, etc.)
                # Many editors (VS Code, Zed, Cursor) use JSONC for config files
                content = f.read()
                raw_config = json5.loads(content)
    except yaml.YAMLError as e:
        logger.warning(
            "Failed to parse config file - invalid YAML",
            client=client_def.name,
            path=str(config_path),
            error=str(e),
        )
        return None
    except ValueError as e:
        # json5 raises ValueError for parse errors
        logger.warning(
            "Failed to parse config file - invalid JSON/JSONC",
            client=client_def.name,
            path=str(config_path),
            error=str(e),
        )
        return None
    except IOError as e:
        logger.warning(
            "Failed to read config file",
            client=client_def.name,
            path=str(config_path),
            error=str(e),
        )
        return None

    # Handle case where YAML file is empty or contains only null
    if raw_config is None:
        logger.debug(
            "Config file is empty or null",
            client=client_def.name,
        )
        return None

    # Get file modification time
    try:
        stat = config_path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        modified_at = None

    # Use the client definition to extract servers from the config
    # This handles client-specific JSON/YAML structures
    mcp_servers = client_def.extract_servers(raw_config)

    # Parse each server entry
    servers: list[MCPServerConfig] = []
    for name, server_config in mcp_servers.items():
        if isinstance(server_config, dict):
            try:
                # Use client-specific parsing for clients with custom formats
                if client_def.name == "goose":
                    server = _parse_goose_extension(name, server_config)
                    if server is not None:
                        servers.append(server)
                elif client_def.name == "zed":
                    server = _parse_zed_context_server(name, server_config)
                    if server is not None:
                        servers.append(server)
                else:
                    server = _parse_server_entry(name, server_config)
                    servers.append(server)
            except Exception as e:
                logger.warning(
                    "Failed to parse server entry",
                    client=client_def.name,
                    server_name=name,
                    error=str(e),
                )
                continue

    if not servers:
        logger.debug(
            "No MCP servers found in config",
            client=client_def.name,
        )
        return None

    logger.debug(
        "Parsed config file",
        client=client_def.name,
        server_count=len(servers),
    )

    return MCPClientConfig(
        client=client_def.name,
        client_version=None,  # TODO: Could detect from app version
        config_path=str(config_path),
        config_modified_at=modified_at,
        servers=servers,
    )
