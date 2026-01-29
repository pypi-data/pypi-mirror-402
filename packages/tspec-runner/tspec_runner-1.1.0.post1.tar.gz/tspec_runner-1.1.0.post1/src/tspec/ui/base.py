from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol

from ..errors import ExecutionError

@dataclass
class UISettings:
    backend: str = "selenium"  # selenium|appium|pywinauto|agent-browser
    headless: bool = True
    implicit_wait_ms: int = 0

class UIDriver(Protocol):
    def open(self, url: str) -> None: ...
    def open_app(self, server_url: str, caps: dict) -> None: ...
    def click(self, selector: str) -> None: ...
    def type(self, selector: str, text: str) -> None: ...
    def wait_for(self, selector: str, text_contains: Optional[str], timeout_ms: int) -> None: ...
    def get_text(self, selector: str) -> str: ...
    def screenshot(self, path: str) -> None: ...
    def close(self) -> None: ...

def ensure_supported_backend(name: str) -> str:
    n = (name or "").strip().lower().replace("_", "-")
    if n in ("selenium", "appium", "pywinauto", "agent-browser"):
        return n
    raise ExecutionError(f"Unknown ui backend: {name!r} (expected selenium|appium|pywinauto|agent-browser)")
