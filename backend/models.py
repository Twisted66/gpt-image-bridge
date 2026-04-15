from pydantic import BaseModel, Field


class GenerateImageRequest(BaseModel):
    prompt: str = Field(min_length=1)
    out_path: str = Field(min_length=1)


class GenerateImageResponse(BaseModel):
    ok: bool
    path: str
    absolute_path: str
    mime_type: str
    width: int | None = None
    height: int | None = None
    message: str
