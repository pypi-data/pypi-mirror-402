from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError as PydanticValidationError

from .errors import ValidationError
from .parser import load_tspec_file
from .manual_model import ManualFile

def _deep_merge(a: Any, b: Any) -> Any:
    if isinstance(a, dict) and isinstance(b, dict):
        r = dict(a)
        for k, v in b.items():
            r[k] = _deep_merge(r[k], v) if k in r else v
        return r
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    return b

def merge_manual_blocks(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for b in blocks:
        out = _deep_merge(out, b)
    return out

def load_manual(path: Path) -> ManualFile:
    parsed = load_tspec_file(path)
    merged = merge_manual_blocks(parsed.blocks)
    try:
        return ManualFile.model_validate(merged)
    except PydanticValidationError as e:
        raise ValidationError(str(e)) from e

def _manual_key_from_path(path: Path) -> str:
    name = path.name
    if name.endswith(".tspec.md"):
        return name[: -len(".tspec.md")]
    return path.stem

def discover_manuals(base: Path) -> List[Tuple[Path, ManualFile]]:
    items: List[Tuple[Path, ManualFile]] = []
    for p in sorted(base.rglob("*.tspec.md")):
        try:
            mf = load_manual(p)
        except Exception:
            continue
        items.append((p, mf))
    return items

def find_manual_by_id(base: Path, manual_id: str) -> Tuple[Path, ManualFile]:
    manual_id = manual_id.strip()
    candidates: List[Tuple[Path, ManualFile]] = []
    for p, mf in discover_manuals(base):
        if mf.manual.id == manual_id:
            return p, mf
        if manual_id in (mf.manual.tags or []):
            candidates.append((p, mf))
            continue
        if _manual_key_from_path(p) == manual_id:
            candidates.append((p, mf))
            continue
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        paths = ", ".join(str(p) for p, _ in candidates)
        raise ValidationError(f"Manual id not found: {manual_id!r} (tag/path matches: {paths})")
    raise ValidationError(f"Manual id not found: {manual_id!r} (searched under {base})")
