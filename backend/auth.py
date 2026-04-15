import os
from fastapi import Header, HTTPException, status


def verify_bearer_token(authorization: str | None = Header(default=None)) -> str:
    """Verify Bearer token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )

    token = authorization[len("Bearer "):].strip()
    allowed = os.environ.get("IMAGE_BRIDGE_ALLOWED_BEARER", "").strip()

    if not allowed or token != allowed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid bearer token",
        )

    return token


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    """Verify API key from X-API-Key header (simpler for Custom GPT Actions)."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing API key",
        )

    allowed = os.environ.get("IMAGE_BRIDGE_API_KEY", "").strip()

    if not allowed or x_api_key != allowed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid API key",
        )

    return x_api_key
