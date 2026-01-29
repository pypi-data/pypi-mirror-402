from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

SUPPORTED_MANUAL_LANGS = {"en", "jp", "ja"}

def normalize_manual_lang(lang: Optional[str]) -> Optional[str]:
    if not lang:
        return None
    l = lang.strip().lower()
    if l in {"ja", "jp"}:
        return "jp"
    if l == "en":
        return "en"
    return l

def manual_lang_from_path(path: Path) -> Optional[str]:
    name = path.name
    if not name.endswith(".tspec.md"):
        return None
    base = name[: -len(".tspec.md")]
    if "." not in base:
        return None
    tail = base.rsplit(".", 1)[-1]
    lang = normalize_manual_lang(tail)
    if lang in {"en", "jp"}:
        return lang
    return None

def _manual_key_from_path(path: Path) -> str:
    name = path.name
    if name.endswith(".tspec.md"):
        base = name[: -len(".tspec.md")]
        if "." in base:
            maybe_lang = base.rsplit(".", 1)[-1]
            if normalize_manual_lang(maybe_lang) in {"en", "jp"}:
                return base[: -(len(maybe_lang) + 1)]
        return base
    return path.stem

def discover_manuals(base: Path, *, lang: Optional[str] = None) -> List[Tuple[Path, ManualFile]]:
    norm_lang = normalize_manual_lang(lang)
    items: List[Tuple[Path, ManualFile]] = []
    for p in sorted(base.rglob("*.tspec.md")):
        if norm_lang and manual_lang_from_path(p) != norm_lang:
            continue
        try:
            mf = load_manual(p)
        except Exception:
            continue
        items.append((p, mf))
    return items

def _pick_candidate(candidates: List[Tuple[Path, ManualFile]], preferred: Optional[str]) -> Tuple[Path, ManualFile]:
    if not candidates:
        raise ValidationError("No manual candidates found")
    if preferred:
        for p, mf in candidates:
            if manual_lang_from_path(p) == preferred:
                return p, mf
    for pref in ("en", None, "jp"):
        for p, mf in candidates:
            if manual_lang_from_path(p) == pref:
                return p, mf
    return candidates[0]

def find_manual_by_id(base: Path, manual_id: str, *, lang: Optional[str] = None) -> Tuple[Path, ManualFile]:
    manual_id = manual_id.strip()
    norm_lang = normalize_manual_lang(lang)
    direct: List[Tuple[Path, ManualFile]] = []
    candidates: List[Tuple[Path, ManualFile]] = []
    for p, mf in discover_manuals(base, lang=norm_lang):
        if mf.manual.id == manual_id:
            direct.append((p, mf))
            continue
        if manual_id in (mf.manual.tags or []):
            candidates.append((p, mf))
            continue
        if _manual_key_from_path(p) == manual_id:
            candidates.append((p, mf))
            continue
    if direct:
        return _pick_candidate(direct, norm_lang)
    if candidates:
        if len(candidates) == 1:
            return candidates[0]
        if norm_lang:
            return _pick_candidate(candidates, norm_lang)
        paths = ", ".join(str(p) for p, _ in candidates)
        langs = sorted({manual_lang_from_path(p) or "default" for p, _ in candidates})
        raise ValidationError(f"Manual id not found: {manual_id!r} (tag/path matches: {paths}; langs: {', '.join(langs)})")
    raise ValidationError(f"Manual id not found: {manual_id!r} (searched under {base})")
