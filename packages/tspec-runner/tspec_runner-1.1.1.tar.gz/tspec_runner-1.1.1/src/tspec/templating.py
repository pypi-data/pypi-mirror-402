from __future__ import annotations

import re
from typing import Any, Dict
from .errors import ValidationError

VAR_RE = re.compile(r"\$\{(?P<path>[A-Za-z0-9_\.]+)\}")

def _get_by_path(ctx: Dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    cur: Any = ctx
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            raise KeyError(path)
    return cur

def render(obj: Any, ctx: Dict[str, Any]) -> Any:
    if obj is None:
        return None
    if isinstance(obj, str):
        def repl(m):
            key = m.group("path")
            try:
                v = _get_by_path(ctx, key)
            except KeyError as e:
                raise ValidationError(f"Unresolved variable: ${{{key}}}") from e
            return str(v)
        return VAR_RE.sub(repl, obj)
    if isinstance(obj, list):
        return [render(x, ctx) for x in obj]
    if isinstance(obj, dict):
        return {k: render(v, ctx) for k, v in obj.items()}
    return obj
