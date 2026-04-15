#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request

BRIDGE_URL = os.environ.get("IMAGE_BRIDGE_URL", "http://127.0.0.1:8787")
OAUTH_TOKEN = os.environ.get("IMAGE_BRIDGE_OAUTH_TOKEN", "")


def send(msg: dict) -> None:
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def call_backend(prompt: str, out_path: str) -> dict:
    if not OAUTH_TOKEN:
        raise RuntimeError("IMAGE_BRIDGE_OAUTH_TOKEN is not set")

    payload = json.dumps({"prompt": prompt, "out_path": out_path}).encode("utf-8")
    req = urllib.request.Request(
        url=f"{BRIDGE_URL.rstrip('/')}/generate-image",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OAUTH_TOKEN}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"backend http {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"backend connection failed: {exc}") from exc


def handle_tool(arguments: dict) -> dict:
    prompt = arguments.get("prompt")
    out_path = arguments.get("out_path")

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt is required")
    if not isinstance(out_path, str) or not out_path.strip():
        raise ValueError("out_path is required")

    result = call_backend(prompt.strip(), out_path.strip())
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result),
            }
        ]
    }


def main() -> None:
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue

        req = json.loads(raw)
        method = req.get("method")
        req_id = req.get("id")

        try:
            if method == "initialize":
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2025-03-26",
                            "capabilities": {"tools": {}},
                            "serverInfo": {
                                "name": "image-bridge-mcp",
                                "version": "0.1.0",
                            },
                        },
                    }
                )
            elif method == "tools/list":
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "tools": [
                                {
                                    "name": "generate_image",
                                    "description": "Generate an image via the shared image bridge backend.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "prompt": {"type": "string"},
                                            "out_path": {"type": "string"},
                                        },
                                        "required": ["prompt", "out_path"],
                                        "additionalProperties": False,
                                    },
                                }
                            ]
                        },
                    }
                )
            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})
                if name != "generate_image":
                    raise ValueError(f"unknown tool: {name}")
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": handle_tool(arguments),
                    }
                )
            else:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"method not found: {method}",
                        },
                    }
                )
        except Exception as exc:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(exc)},
                }
            )


if __name__ == "__main__":
    main()
