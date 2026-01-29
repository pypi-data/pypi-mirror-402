# Runlayer Verified Local Proxy

A security-focused MCP proxy that verifies code signatures before forwarding traffic to local MCP servers.

Can be run as a local MCP server from Runlayer. Servers such as the Figma desktop MCP run locally on a preconfigured port, leaving that traffic susceptible to other processes being spin up on that port.

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────┐     ┌─────────────────┐
│   MCP Client    │     │   Verified Local Proxy           │     │  Local MCP      │
│   (Claude)      │────▶│                                  │────▶│  Server         │
│                 │     │  1. Find process on port         │     │  (e.g. Figma)   │
└─────────────────┘     │  2. Verify code signature        │     └─────────────────┘
                        │  3. Check certificate chain      │
       stdio            │  4. Proxy MCP traffic            │        HTTP/SSE
                        │  5. Periodic re-verification     │
                        └──────────────────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Watchdog Thread │
                              │ (kill if stuck) │
                              └─────────────────┘
```

## Security Features

| Feature | Description |
|---------|-------------|
| **Code Signature Verification** | Verifies macOS `codesign` signatures |
| **Certificate Chain Validation** | Ensures root CA is trusted (e.g., Apple Root CA) |
| **Exact Authority Matching** | Prevents spoofing with similar certificate names |
| **Periodic Re-verification** | Mitigates TOCTOU attacks by re-checking signatures |
| **Watchdog Thread** | Terminates proxy if re-verification gets stuck |
| **Path Hijacking Prevention** | Uses absolute paths to SIP-protected system binaries |
| **Subprocess Hardening** | List arguments, timeouts, no shell execution |

## Usage

```bash
# List available servers
uvx runlayer-verified-local-proxy --list-servers

# Run proxy for Figma
uvx runlayer-verified-local-proxy --server-id com.figma/desktop-mcp

# Verbose mode
uvx runlayer-verified-local-proxy --server-id com.figma/desktop-mcp -v
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "figma": {
      "command": "uvx",
      "args": ["runlayer-verified-local-proxy", "--server-id", "com.figma/desktop-mcp"]
    }
  }
}
```

## Configuration

Server configs are defined in `config.py`. Example:

```python
VerificationConfig(
    server_id="com.figma/desktop-mcp",
    display_name="Figma Desktop MCP",
    target_port=3845,
    target_path="/sse",

    # macOS verification (team ID embedded in authority string)
    macos_authority="Developer ID Application: Figma, Inc. (T8RA8NE3B7)",
    macos_root_ca="Apple Root CA",

    # Security options
    reverify_interval_seconds=10,      # Re-verify every 10s
    macos_strict_resource_check=False, # Skip sealed resources (Electron apps)

    # Resilience options
    wait_for_target=True,              # Wait for target to start
    retry_on_target_loss=True,         # Survive target restarts
)
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Normal exit |
| 1 | Configuration error |
| 2 | Signature verification failed |
| 3 | Target not running |

## Follow-ups

<!-- TODO: Discuss and prioritize -->

- [ ] Cross-platform support (Windows feasible)
- [ ] Fetch verification configs from Runlayer server configuration (API? stdio?)
- [ ] Distribute server package
