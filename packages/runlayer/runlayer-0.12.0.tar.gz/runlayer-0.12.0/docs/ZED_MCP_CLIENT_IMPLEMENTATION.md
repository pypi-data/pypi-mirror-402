# Zed MCP Client Implementation

## Overview

This document details the implementation of Zed editor support for the MCP Watch scan CLI. The implementation enables scanning for MCP server configurations in Zed, including global settings, project-level settings, and installed MCP extensions.

## Changes Summary

| File | Lines Changed | Description |
|------|---------------|-------------|
| `cli/runlayer_cli/scan/clients.py` | +63 | Added `ExtensionsPath` dataclass and Zed client definition |
| `cli/runlayer_cli/scan/config_parser.py` | +108 | Added JSONC comment stripping and Zed-specific parsing |
| `cli/runlayer_cli/scan/service.py` | +119 | Added extensions folder scanning and merging logic |
| `cli/tests/test_scan_clients.py` | +87 | Added Zed client and ExtensionsPath tests |
| `cli/tests/test_scan_parser.py` | +400 | Added Zed parsing and JSONC comment tests |

**Total: 774 lines added**

## Implementation Details

### 1. ExtensionsPath Dataclass (`clients.py`)

Added a new dataclass to support scanning extension directories:

```python
@dataclass
class ExtensionsPath:
    """Path to extensions directory with prefix pattern for folder scanning."""
    path: str
    platform: str = "all"
    prefix: str = "mcp-server"

    def resolve(self) -> Path | None:
        """Resolve the path for the current platform."""
        # Platform-aware path resolution with env var expansion
```

Added `extensions_paths` field to `MCPClientDefinition` to support clients with extension directories.

### 2. Zed Client Definition (`clients.py`)

Added Zed to the `MCP_CLIENTS` registry:

```python
MCPClientDefinition(
    name="zed",
    display_name="Zed",
    paths=[
        ConfigPath("~/.config/zed/settings.json", platform="macos"),
        ConfigPath("%APPDATA%/Zed/settings.json", platform="windows"),
    ],
    servers_key="context_servers",
    project_config=ProjectConfigPattern(
        relative_path=".zed/settings.json",
        servers_key="context_servers",
    ),
    extensions_paths=[
        ExtensionsPath(
            "~/Library/Application Support/Zed/extensions/installed",
            platform="macos",
            prefix="mcp-server",
        ),
        ExtensionsPath(
            "%LOCALAPPDATA%/Zed/extensions/installed",
            platform="windows",
            prefix="mcp-server",
        ),
    ],
)
```

**Key differences from other clients:**
- Uses `context_servers` key (not `mcpServers`)
- Has extension folder scanning for `mcp-server-*` directories
- Supports both macOS and Windows paths

### 3. JSONC Comment Stripping (`config_parser.py`)

Added support for JSON with Comments (JSONC) which is used by Zed, VS Code, and other editors:

```python
def _strip_json_comments(content: str) -> str:
    """Strip JavaScript-style comments from JSON content."""
    # Remove UTF-8 BOM if present (common on Windows)
    if content.startswith("\ufeff"):
        content = content[1:]
    
    # Remove block comments /* ... */
    content = re.sub(r"/\*[\s\S]*?\*/", "", content)
    
    # Remove single-line comments // ...
    # Handles comments outside of strings
    ...
```

**Handles:**
- Single-line comments: `// comment`
- Block comments: `/* comment */`
- UTF-8 BOM (Byte Order Mark) - common on Windows

This is applied to **all JSON config files** (not just Zed) to ensure compatibility with any editor that uses JSONC.

### 4. Zed-Specific Server Parsing (`config_parser.py`)

Added `_parse_zed_context_server()` function:

```python
def _parse_zed_context_server(name: str, config: dict[str, Any]) -> MCPServerConfig | None:
    """Parse a Zed context_servers entry.
    
    Handles:
    - 'enabled': bool (skip if false, defaults to true)
    - 'command'/'args'/'env': stdio transport
    - 'url': SSE transport
    - 'settings': extension config (skipped - no command/url)
    """
```

**Behavior:**
- Servers with `enabled: false` are skipped
- Servers with only `settings` (no `command`/`url`) are skipped (extension placeholders)
- Defaults `enabled` to `true` if not specified

### 5. Extensions Folder Scanning (`service.py`)

Added two new functions:

```python
def scan_extensions_folder(client_def: MCPClientDefinition) -> list[str]:
    """Scan extensions folder for MCP server directories.
    
    Returns list of folder names matching the prefix (e.g., "mcp-server-*").
    """

def merge_extensions_with_config(
    config: MCPClientConfig,
    extension_names: list[str],
) -> None:
    """Merge discovered extensions into config.
    
    Extensions not already in settings.json are added as stdio servers
    with command=None (extension handles invocation internally).
    """
```

**Integration in `scan_all_clients()`:**
1. After parsing a client's config file, check if it has `extensions_paths`
2. Scan the extensions folder for `mcp-server-*` directories
3. Merge any extensions not already in the config
4. Handle case where no config file exists but extensions do

### 6. Zed Settings Format

Zed uses `context_servers` for MCP configuration:

```json
{
  "context_servers": {
    "my-stdio-server": {
      "enabled": true,
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-test"],
      "env": {}
    },
    "my-remote-server": {
      "enabled": true,
      "url": "https://example.com/mcp"
    },
    "mcp-server-context7": {
      "enabled": true,
      "settings": {
        "context7_api_key": ""
      }
    }
  }
}
```

## Test Coverage

### New Test Classes

| Test Class | Tests | Description |
|------------|-------|-------------|
| `TestExtensionsPath` | 5 | ExtensionsPath dataclass functionality |
| `TestParseZedConfig` | 9 | Zed context_servers parsing |
| `TestStripJsonComments` | 7 | JSONC comment stripping |

### New Test Methods

**In `TestClientServersKey`:**
- `test_zed_uses_context_servers_key`
- `test_zed_has_project_config`
- `test_zed_has_extensions_paths`
- `test_zed_extract_servers`

**In `TestGetAllClients`:**
- Updated `test_includes_known_clients` to include "zed"

**In `TestGetClientsWithProjectConfigs`:**
- Updated `test_includes_expected_clients` to include "zed"

**JSONC tests for other clients:**
- `test_parses_cursor_config_with_comments`
- `test_parses_vscode_config_with_comments`
- `test_parses_windsurf_config_with_comments`

## Configuration Paths

| Platform | Settings Path | Extensions Path |
|----------|--------------|-----------------|
| macOS | `~/.config/zed/settings.json` | `~/Library/Application Support/Zed/extensions/installed/` |
| Windows | `%APPDATA%/Zed/settings.json` | `%LOCALAPPDATA%/Zed/extensions/installed/` |
| Project | `.zed/settings.json` | N/A |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     scan_all_clients()                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐                   │
│  │ Global Settings │    │ Extensions Folder │                   │
│  │ settings.json   │    │ mcp-server-*      │                   │
│  └────────┬────────┘    └────────┬─────────┘                   │
│           │                      │                              │
│           ▼                      ▼                              │
│  ┌─────────────────┐    ┌──────────────────┐                   │
│  │ parse_config    │    │ scan_extensions  │                   │
│  │ (with JSONC)    │    │ folder           │                   │
│  └────────┬────────┘    └────────┬─────────┘                   │
│           │                      │                              │
│           └──────────┬───────────┘                              │
│                      ▼                                          │
│           ┌──────────────────┐                                  │
│           │ merge_extensions │                                  │
│           │ with_config      │                                  │
│           └────────┬─────────┘                                  │
│                    │                                            │
│                    ▼                                            │
│           ┌──────────────────┐                                  │
│           │ MCPClientConfig  │                                  │
│           │ (deduplicated)   │                                  │
│           └──────────────────┘                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Breaking Changes

None. This is a purely additive change.

## Future Considerations

1. **Extension metadata parsing**: Currently we only detect extension folder names. In the future, we could parse extension manifests for additional metadata.

2. **Linux support**: Zed is available on Linux but paths need verification.

3. **Zed Preview/Nightly**: Different Zed editions may use different paths.






