import os
from pathlib import Path


def get_output_root() -> Path:
    root = os.environ.get("IMAGE_BRIDGE_OUTPUT_ROOT", "").strip()
    if not root:
        raise RuntimeError("IMAGE_BRIDGE_OUTPUT_ROOT is not set")
    path = Path(root).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_target(out_path: str) -> Path:
    root = get_output_root()
    relative = Path(out_path)
    if relative.is_absolute():
        raise ValueError("out_path must be relative")
    target = (root / relative).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("out_path escapes output root")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def write_bytes(target: Path, data: bytes) -> None:
    target.write_bytes(data)
