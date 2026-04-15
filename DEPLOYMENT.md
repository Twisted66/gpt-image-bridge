# GPT Image Bridge Deployment Guide

Deploy your FastAPI backend to Render and connect it to a Custom GPT.

---

## Quick Start

1. Push code to GitHub
2. Connect repo to [Render](https://render.com)
3. Set environment variables
4. Deploy and copy the HTTPS URL
5. Configure Custom GPT Action

---

## Step 1: Prepare Your Repository

Ensure your repo structure looks like this:

```
gpt-codex-image-bridge/
├── backend/
│   ├── app.py              # FastAPI app (with CORS + dual auth)
│   ├── auth.py             # Bearer + API key auth
│   ├── models.py           # Pydantic models
│   ├── storage.py          # File storage logic
│   ├── requirements.txt    # Python dependencies
│   ├── start.sh            # Render startup script
│   ├── .renderignore       # Files to exclude from deploy
│   └── .env.example        # Environment template
├── openapi.yaml            # OpenAPI spec for GPT Actions
├── render.yaml             # Render Blueprint config
└── DEPLOYMENT.md           # This file
```

---

## Step 2: Create Render Account & Service

### Option A: Deploy via Blueprint (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repo
4. Render will read `render.yaml` and create the service automatically

### Option B: Manual Web Service

1. Click **"New"** → **"Web Service"**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `gpt-image-bridge` (or your choice)
   - **Environment**: Python 3
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
   - **Plan**: Free

---

## Step 3: Configure Environment Variables

In your Render service dashboard, go to **Environment** and add:

| Variable | Value | Required |
|----------|-------|----------|
| `IMAGE_BRIDGE_API_KEY` | `your-secure-api-key-here` | **Yes** |
| `IMAGE_BRIDGE_ALLOWED_BEARER` | `your-bearer-token-here` | Optional |
| `CORS_ORIGINS` | `https://chat.openai.com,https://chatgpt.com` | Recommended |

### Generating a Secure API Key

```bash
# On Linux/Mac
openssl rand -hex 32

# On Windows PowerShell
[Convert]::ToHexString((1..32 | ForEach-Object { Get-Random -Maximum 256 } | ForEach-Object { [byte]$_ }))
```

Copy the generated key into `IMAGE_BRIDGE_API_KEY`.

---

## Step 4: Deploy

1. Click **"Deploy"** (or push to main branch for auto-deploy)
2. Wait for build to complete (~2-3 minutes)
3. Note your service URL: `https://gpt-image-bridge-xxx.onrender.com`

### Test the Deployment

```bash
curl https://gpt-image-bridge-xxx.onrender.com/health
# Expected: {"ok":true}
```

---

## Step 5: Configure Custom GPT Action

### 1. Create a New GPT

1. Go to [ChatGPT](https://chat.openai.com)
2. Click **"Explore GPTs"** → **"Create"**
3. Name it: `Image Generator`
4. Add instructions (example below)

### 2. Add the Action

1. Click **"Add Actions"**
2. Click **"Import from URL"** or paste the OpenAPI schema from `openapi.yaml`
3. **Authentication**: Choose **"API Key"**
   - **Header Name**: `X-API-Key`
   - **API Key**: Paste your `IMAGE_BRIDGE_API_KEY` value
4. Save

### 3. GPT Instructions Template

```markdown
You are an image generation assistant.

When the user asks you to create an image:
1. Use the generateImage action to create the image
2. Provide a descriptive prompt based on their request
3. The image will be saved to the specified path

Example:
User: "Create a sunset image and save it to /images/sunset.png"
→ Call generateImage with {"prompt": "Beautiful sunset over mountains with orange sky", "out_path": "/images/sunset.png"}
```

---

## Authentication Options

### Option A: API Key (Recommended for Custom GPT)

- Simplest to configure
- Works with GPT Actions native API key support
- Header: `X-API-Key: your-api-key`

### Option B: Bearer Token

- OAuth-like experience
- Header: `Authorization: Bearer your-token`

### Option C: OAuth 2.0 (Advanced)

If you need OAuth, you'll need to:
1. Set up an OAuth provider (Auth0, Clerk, etc.)
2. Update `openapi.yaml` with your OAuth URLs
3. Configure GPT Action with OAuth flow

---

## Free Tier Limitations

| Feature | Limit |
|---------|-------|
| **Uptime** | Spins down after 15 min idle |
| **Cold Start** | ~30 seconds after idle |
| **RAM** | 512 MB |
| **CPU** | 0.1 vCPU |
| **Requests** | No limit, but slower when busy |

### Tips for Free Tier

- The first request after idle will be slow (cold start)
- Keep prompts simple for faster generation
- Consider upgrading if you need consistent performance

---

## Troubleshooting

### Deployment Fails

```bash
# Check logs in Render dashboard
# Common issues:
# 1. Missing requirements.txt - ensure it's in backend/
# 2. start.sh not executable - run: chmod +x backend/start.sh
```

### 401 Unauthorized

- Verify `IMAGE_BRIDGE_API_KEY` is set in Render dashboard
- Check that GPT Action uses correct header: `X-API-Key`
- Test with curl: `curl -H "X-API-Key: your-key" https://your-app.onrender.com/health`

### CORS Errors

- Add your origin to `CORS_ORIGINS` environment variable
- Use `*` only for testing, specify actual origins in production

### Image Generation Not Implemented

- The `/generate-image` endpoint is ready but needs an image provider
- Implement `generate_image_bytes()` in `backend/providers/generator.py`
- See provider examples below

---

## Provider Implementation

To make image generation work, implement `generate_image_bytes()` in `backend/providers/generator.py`:

### Example with OpenAI DALL-E

```python
import os
from openai import OpenAI

def generate_image_bytes(prompt: str) -> tuple[bytes, str, int, int]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        response_format="b64_json"
    )

    import base64
    image_data = base64.b64decode(response.data[0].b64_json)

    return image_data, "image/png", 1024, 1024
```

### Example with Stability AI

```python
import os
import requests

def generate_image_bytes(prompt: str) -> tuple[bytes, str, int, int]:
    api_key = os.environ["STABILITY_API_KEY"]
    response = requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/sd3",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"none": ""},
        data={"prompt": prompt, "output_format": "png"}
    )
    response.raise_for_status()
    return response.content, "image/png", 1024, 1024
```

---

## Security Checklist

- [ ] `IMAGE_BRIDGE_API_KEY` is a secure random string (32+ chars)
- [ ] Environment variables are set in Render, not in code
- [ ] CORS origins restricted to OpenAI domains in production
- [ ] `.renderignore` excludes `.env` files
- [ ] Bearer token rotated regularly (if used)

---

## Next Steps

1. **Add image provider** to `backend/providers/generator.py`
2. **Test end-to-end** with your Custom GPT
3. **Add rate limiting** if needed (consider upgrading plan)
4. **Monitor usage** in Render dashboard

---

## Support

- [Render Docs](https://render.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [OpenAI GPT Actions](https://platform.openai.com/docs/actions)
