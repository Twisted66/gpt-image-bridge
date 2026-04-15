from typing import Literal
from pydantic import BaseModel, Field



class GenerateImageRequest(BaseModel):
    # Prompt: 1-2000 chars, no empty prompts
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The text prompt for image generation."
    )
    # out_path: Relative path, alphanumeric/underscores/dashes/dots only. 
    # Prevents traversal and shell-injection characters.
    out_path: str = Field(
        ...,
        min_length=1,
        pattern=r"^[a-zA-Z0-9_\-\./]+\.(png|jpg|jpeg|webp)$",
        description="Relative path and filename (e.g., 'outputs/hero.png'). Must end in a supported image extension."
    )


class BatchGenerateImageRequest(BaseModel):
    style_anchor: str | None = Field(
        None,
        max_length=1000,
        description="A style description to be prepended to each item's prompt for consistency."
    )
    items: list[GenerateImageRequest] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="A list of images to generate."
    )


class GenerateImageResponse(BaseModel):
    ok: bool = Field(..., description="Whether the operation was successful.")
    path: str = Field(..., description="The relative path requested.")
    absolute_path: str = Field(..., description="The resolved absolute path on the server.")
    mime_type: str = Field(..., description="The MIME type of the generated image.")
    width: int | None = Field(None, description="Width in pixels.")
    height: int | None = Field(None, description="Height in pixels.")
    message: str = Field(..., description="A status message.")


class BatchGenerateImageResponse(BaseModel):
    ok: bool = Field(..., description="Whether the overall operation was successful.")
    results: list[GenerateImageResponse] = Field(..., description="Detailed results for each item.")
    message: str = Field(..., description="Summary status message.")


class ErrorDetail(BaseModel):
    loc: list[str | int] | None = Field(None, description="Location of the error (e.g., ['body', 'prompt']).")
    msg: str = Field(..., description="A human-readable error message.")
    type: str = Field(..., description="The type of error (e.g., 'value_error.missing').")



class ErrorResponse(BaseModel):
    ok: Literal[False] = Field(False, description="Whether the operation was successful (always false for errors).")
    error: str = Field(..., description="A high-level error code or summary.")
    details: list[ErrorDetail] | None = Field(None, description="Structured error details.")
