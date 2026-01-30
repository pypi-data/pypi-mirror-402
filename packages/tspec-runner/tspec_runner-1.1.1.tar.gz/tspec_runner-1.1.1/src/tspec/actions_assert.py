from __future__ import annotations

import re
from typing import Any, Dict
from .errors import ExecutionError

def equals(args: Dict[str, Any]) -> None:
    left = args.get("left")
    right = args.get("right")
    msg = args.get("message") or f"Expected {left!r} == {right!r}"
    if left != right:
        raise ExecutionError(msg)

def true(args: Dict[str, Any]) -> None:
    value = args.get("value")
    msg = args.get("message") or f"Expected truthy value, got {value!r}"
    if not value:
        raise ExecutionError(msg)

def contains(args: Dict[str, Any]) -> None:
    text = args.get("text", "")
    sub = args.get("substring")
    msg = args.get("message") or f"Expected {sub!r} to be in {text!r}"
    if sub not in text:
        raise ExecutionError(msg)

def matches(args: Dict[str, Any]) -> None:
    text = args.get("text", "")
    pattern = args.get("regex")
    msg = args.get("message") or f"Expected {text!r} to match /{pattern}/"
    if pattern is None:
        raise ExecutionError("regex is required")
    if re.search(pattern, text) is None:
        raise ExecutionError(msg)
