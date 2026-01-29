from __future__ import annotations

import re
from typing import Optional, Tuple

_SELECTOR_BY = {
    "css": "css selector",
    "xpath": "xpath",
    "id": "id",
    "name": "name",
    "link": "link text",
    "link_text": "link text",
    "partial_link": "partial link text",
    "partial_link_text": "partial link text",
    "tag": "tag name",
    "class": "class name",
}


def parse_selector(raw: str) -> Tuple[str, str]:
    selector = (raw or "").strip()
    if not selector:
        raise ValueError("selector is empty")
    if "=" in selector:
        prefix, value = selector.split("=", 1)
        key = prefix.strip().lower()
        if key in _SELECTOR_BY:
            return _SELECTOR_BY[key], value
    return _SELECTOR_BY["css"], selector


def parse_window_size(raw: Optional[str]) -> Optional[Tuple[int, int]]:
    if not raw:
        return None
    s = str(raw).strip().lower().replace("x", " ").replace(",", " ")
    parts = [p for p in s.split() if p]
    if len(parts) != 2:
        raise ValueError(f"invalid window_size: {raw!r}")
    width, height = int(parts[0]), int(parts[1])
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid window_size: {raw!r}")
    return width, height


def extract_major_version(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"(\d+)(?:\.\d+){1,3}", text)
    if not match:
        return None
    return int(match.group(1))
