# GPT Action + Local Codex CLI MCP Bridge

This package gives you the **full bridge system** for your stated goal:

1. **Custom GPT Action**
2. **Local MCP bridge**
3. **Tool callable from local Codex CLI**

## What this package contains

- `openapi.yaml` — import into your custom GPT as an Action
- `backend/` — shared HTTP backend used by both GPT Action and MCP
- `mcp/mcp_server.py` — local MCP server for Codex CLI
- `codex/config.toml.example` — Codex MCP config example
- `scripts/` — helper run commands

## System layout

```text
Custom GPT
  -> Action (OAuth)
  -> POST /generate-image
  -> shared backend

Local Codex CLI
  -> MCP tool generate_image(prompt, out_path)
  -> same POST /generate-image
  -> same shared backend
```

## Important boundary

This package gives you the **bridge architecture and runnable adapters**.

The file `backend/providers/generator.py` is the single provider hook where your actual image generation implementation goes.

That separation is intentional:
- bridge/auth/mcp/action wiring is complete here
- actual image generation engine is isolated to one file

## File tree

```text
gpt-codex-image-bridge/
├── README.md
├── openapi.yaml
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── models.py
│   ├── storage.py
│   ├── requirements.txt
│   └── providers/
│       └── generator.py
├── mcp/
│   └── mcp_server.py
├── codex/
│   └── config.toml.example
└── scripts/
    ├── run_backend.sh
    └── run_mcp.sh
```

## 1) Backend setup

### Requirements

- Python 3.10+
- A reachable HTTPS host for the backend if your GPT Action will call it remotely

### Install

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment

Set these environment variables before starting the backend:

```bash
export IMAGE_BRIDGE_ALLOWED_BEARER="replace-with-real-oauth-access-token-for-local-testing"
export IMAGE_BRIDGE_OUTPUT_ROOT="$(pwd)/../generated"
```

Notes:
- `IMAGE_BRIDGE_ALLOWED_BEARER` is a **minimal local validation hook** for testing.
- Replace `auth.py` with your real OAuth token validation when wiring your actual auth provider.
- `IMAGE_BRIDGE_OUTPUT_ROOT` is where generated assets are written.

### Run backend

```bash
../scripts/run_backend.sh
```

Or:

```bash
uvicorn app:app --host 0.0.0.0 --port 8787
```

Backend endpoint:

- `POST /generate-image`

Request body:

```json
{
  "prompt": "dark neon SaaS hero illustration",
  "out_path": "assets/hero/landing-hero.png"
}
```

## 2) Provider hook

Edit this file:

```text
backend/providers/generator.py
```

Implement this function:

```python
def generate_image_bytes(prompt: str) -> tuple[bytes, str, int | None, int | None]:
```

It must return:
- raw image bytes
- mime type
- width
- height

The backend will write those bytes to `out_path` under `IMAGE_BRIDGE_OUTPUT_ROOT`.

## 3) Custom GPT Action setup

In the GPT editor:

1. Add a new Action
2. Paste in `openapi.yaml`
3. Choose **OAuth**
4. Set:
   - Authorization URL
   - Token URL
   - Client ID
   - Client secret
   - Scope: `image.generate`
5. Register the callback URL shown by ChatGPT in your OAuth provider
6. Set the server URL in `openapi.yaml` to your deployed backend URL

The backend currently expects a Bearer token in `Authorization`.

For real OAuth validation, replace the minimal check in `backend/auth.py`.

## 4) Local Codex CLI MCP setup

### MCP server environment

Set:

```bash
export IMAGE_BRIDGE_URL="http://127.0.0.1:8787"
export IMAGE_BRIDGE_OAUTH_TOKEN="replace-with-valid-bearer-token"
```

### Codex MCP config

Copy `codex/config.toml.example` into your Codex config or merge it into:

- `~/.codex/config.toml`
- or project `.codex/config.toml`

### Run the MCP server directly

```bash
./scripts/run_mcp.sh
```

## 5) Codex usage

After Codex picks up the MCP server, the tool exposed to Codex is:

- `generate_image(prompt, out_path)`

Example prompt inside Codex CLI:

```text
Use generate_image to create assets/hero/landing-hero.png with a futuristic dark SaaS hero illustration.
```

## 6) Local testing flow

### Start backend

```bash
cd backend
source .venv/bin/activate
export IMAGE_BRIDGE_ALLOWED_BEARER="dev-token"
export IMAGE_BRIDGE_OUTPUT_ROOT="$(pwd)/../generated"
uvicorn app:app --host 0.0.0.0 --port 8787
```

### Start MCP server environment

```bash
export IMAGE_BRIDGE_URL="http://127.0.0.1:8787"
export IMAGE_BRIDGE_OAUTH_TOKEN="dev-token"
```

### Test backend directly

```bash
curl -X POST http://127.0.0.1:8787/generate-image \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test prompt","out_path":"assets/test.png"}'
```

## 7) What each file does

### `openapi.yaml`
Defines the GPT Action contract.

### `backend/app.py`
HTTP entrypoint. Validates request, verifies bearer token, calls provider hook, writes output file, returns metadata.

### `backend/auth.py`
Very small bearer-token validator stub.

### `backend/storage.py`
Normalizes and writes files under the allowed output root.

### `backend/providers/generator.py`
Only place where actual generation logic belongs.

### `mcp/mcp_server.py`
Exposes `generate_image(prompt, out_path)` to Codex CLI and forwards the call to the backend.

### `codex/config.toml.example`
Example Codex MCP configuration.

## 8) What you edit first

Only these three places usually need edits:

1. `openapi.yaml` — set your real HTTPS backend URL
2. `backend/auth.py` — replace local bearer check with your real OAuth validation
3. `backend/providers/generator.py` — plug in your actual image generation implementation

## 9) Output behavior

Successful responses look like this:

```json
{
  "ok": true,
  "path": "assets/hero/landing-hero.png",
  "absolute_path": "/.../generated/assets/hero/landing-hero.png",
  "mime_type": "image/png",
  "width": 1024,
  "height": 1024,
  "message": "image written"
}
```

## 10) Packaging note

This zip is intentionally split into adapters and backend so you can:
- keep one source of truth for the tool logic
- expose the same operation to both custom GPT and Codex CLI
- call the tool directly from local Codex CLI through MCP
