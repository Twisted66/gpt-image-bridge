#!/bin/bash
# Start script for Render deployment
# Runs the FastAPI app with uvicorn

set -e

echo "Starting Image Bridge API..."

# Get port from environment or default to 8000
PORT="${PORT:-8000}"

# Run uvicorn with production settings
# --proxy-headers: Trust X-Forwarded-Proto from reverse proxy
# --forwarded-allow-ips: Allow all forwarded requests (required for Render)
exec uvicorn app:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --proxy-headers \
    --forwarded-allow-ips '*'
