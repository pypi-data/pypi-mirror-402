from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import List

from .errors import ExecutionError


def list_assets() -> List[str]:
    try:
        pkg = __package__  # tspec
        root = resources.files(pkg) / "assets"
        return sorted([p.name for p in root.iterdir() if p.is_file()])
    except Exception as e:  # pragma: no cover
        raise ExecutionError(f"assets not available: {e}") from e


def extract_asset(name: str, to: Path) -> Path:
    try:
        pkg = __package__  # tspec
        p = resources.files(pkg) / "assets" / name
        if not p.is_file():
            raise ExecutionError(f"asset not found: {name}")
        to.parent.mkdir(parents=True, exist_ok=True)
        to.write_bytes(p.read_bytes())
        return to
    except Exception as e:  # pragma: no cover
        raise ExecutionError(f"failed to extract asset: {e}") from e
