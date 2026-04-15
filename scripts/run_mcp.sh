#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../mcp"
python3 mcp_server.py
