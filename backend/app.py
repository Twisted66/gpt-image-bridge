import os

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import verify_api_key, verify_bearer_token
from models import (
    BatchGenerateImageRequest,
    BatchGenerateImageResponse,
    ErrorResponse,
    GenerateImageRequest,
    GenerateImageResponse,
)

from providers.generator import generate_image_bytes
from storage import resolve_target, write_bytes

app = FastAPI(
    title="Image Bridge API",
    version="1.0.0",
    description="API for generating images via AI and saving them to a specified path. Designed for Custom GPT Actions integration.",
)

# Configure CORS
cors_origins = os.environ.get("CORS_ORIGINS", "https://chat.openai.com,https://chatgpt.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (400) with a structured response."""
    details = [{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            ok=False,
            error="Validation Error",
            details=details
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle standard HTTP errors (401, 403, 500) with a structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            ok=False,
            error=exc.detail,
        ).model_dump()
    )



def verify_auth(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Verify either Bearer token or API key authentication."""
    if x_api_key:
        try:
            return verify_api_key(x_api_key)
        except HTTPException:
            pass

    if authorization:
        try:
            return verify_bearer_token(authorization)
        except HTTPException:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="authentication required - provide either X-API-Key header or Bearer token",
    )


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"ok": True}


@app.post(
    "/generate-image",
    response_model=GenerateImageResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
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
            detail=f"Invalid path: {exc}",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration error: {exc}",
        ) from exc

    try:
        raw, mime_type, width, height = generate_image_bytes(payload.prompt)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Provider not implemented: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {exc}",
        ) from exc

    try:
        write_bytes(target, raw)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File storage failed: {exc}",
        ) from exc

    return GenerateImageResponse(
        ok=True,
        path=payload.out_path,
        absolute_path=str(target),
        mime_type=mime_type,
        width=width,
        height=height,
        message="image written successfully",
    )

@app.post(
    "/generate-images",
    response_model=BatchGenerateImageResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
def batch_generate_images(
    payload: BatchGenerateImageRequest,
    _token: str = Depends(verify_auth),
) -> BatchGenerateImageResponse:
    """Generate multiple images in a batch."""
    results = []
    style_anchor = payload.style_anchor or ""
    
    for item in payload.items:
        # Prepend style anchor if provided
        full_prompt = f"{style_anchor.strip()} {item.prompt.strip()}".strip()
        
        try:
            target = resolve_target(item.out_path)
            raw, mime_type, width, height = generate_image_bytes(full_prompt)
            write_bytes(target, raw)
            
            results.append(GenerateImageResponse(
                ok=True,
                path=item.out_path,
                absolute_path=str(target),
                mime_type=mime_type,
                width=width,
                height=height,
                message="image written successfully",
            ))
        except Exception as exc:
            # For batch, we might want to continue or fail. 
            # In this simple bridge, let's fail fast if one fails to keep it clean for the GPT.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch item failed ({item.out_path}): {exc}",
            )

    return BatchGenerateImageResponse(
        ok=True,
        results=results,
        message=f"successfully generated {len(results)} images",
    )
