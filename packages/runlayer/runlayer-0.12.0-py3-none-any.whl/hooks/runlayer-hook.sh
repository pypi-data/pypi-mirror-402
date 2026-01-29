#!/bin/bash
# Runlayer Cursor Hook - MCP execution validation
#
# This script is installed by: runlayer setup hooks --client cursor --install --secret <key> --host <url>
# Placeholders are replaced during installation.
#
# Supported hooks:
# - beforeMCPExecution (MCP traffic validation)

set -euo pipefail

# Configuration (replaced during installation)
RUNLAYER_API_KEY="__RUNLAYER_API_KEY__"
RUNLAYER_API_HOST="__RUNLAYER_API_HOST__"

input=$(cat)
hook_type=$(echo "$input" | jq -r '.hook_event_name // empty')

case "$hook_type" in
  beforeMCPExecution)
    curl -s -X POST "${RUNLAYER_API_HOST}/api/v1/hooks/cursor" \
      -H "Content-Type: application/json" \
      -H "x-runlayer-api-key: ${RUNLAYER_API_KEY}" \
      -d "$input"
    ;;
esac
