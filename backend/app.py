import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from auth import verify_api_key, verify_bearer_token
from models import GenerateImageRequest, GenerateImageResponse
from providers.generator import generate_image_bytes
from storage import resolve_target, write_bytes

app = FastAPI(
    title="Image Bridge API",
    version="1.0.0",
    description="API for generating images via AI and saving them to a specified path. Designed for Custom GPT Actions integration.",
)

# Configure CORS
cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def verify_auth(
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> str:
    """Verify either Bearer token or API key authentication."""
    # Try API key first (simpler for Custom GPT)
    if x_api_key:
        try:
            return verify_api_key(x_api_key)
        except HTTPException:
            pass

    # Fall back to Bearer token
    if authorization:
        try:
            return verify_bearer_token(authorization)
        except HTTPException:
            pass

    # Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="authentication required - provide either X-API-Key header or Bearer token",
    )


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"ok": True}


@app.post("/generate-image", response_model=GenerateImageResponse)
def generate_image(
    payload: GenerateImageRequest,
    _token: str = Depends(verify_auth),
) -> GenerateImageResponse:
    """Generate an image from a prompt and save it to the specified path."""
    try:
        target = resolve_target(payload.out_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    try:
        raw, mime_type, width, height = generate_image_bytes(payload.prompt)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"provider failed: {exc}",
        ) from exc

    write_bytes(target, raw)

    return GenerateImageResponse(
        ok=True,
        path=payload.out_path,
        absolute_path=str(target),
        mime_type=mime_type,
        width=width,
        height=height,
        message="image written",
    )
