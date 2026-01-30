from __future__ import annotations

from typing import Optional

from ..errors import ExecutionError
from .base import UIDriver, UISettings

class PyWinAutoUIDriver(UIDriver):
    def __init__(self, ui: UISettings):
        try:
            from pywinauto.application import Application  # noqa: F401
        except Exception as e:
            raise ExecutionError(
                "pywinauto backend selected but pywinauto is not installed. "
                "Install with: pip install -e '.[pywinauto]' (Windows only)"
            ) from e
        self.Application = __import__("pywinauto.application", fromlist=["Application"]).Application  # type: ignore
        self.app = None
        self.dlg = None
        self.ui = ui

    def open(self, url: str) -> None:
        raise ExecutionError("open(url) is not supported on pywinauto backend. Use open_app with 'caps'.")

    def open_app(self, server_url: str, caps: dict) -> None:
        # Interpret server_url as 'backend' e.g. 'uia'/'win32'; caps should include 'cmd' or 'exe'
        backend = server_url or "uia"
        cmd = caps.get("cmd") or caps.get("exe")
        if not cmd:
            raise ExecutionError("pywinauto open_app requires caps.cmd or caps.exe")
        self.app = self.Application(backend=backend).start(cmd)
        title = caps.get("title")
        if title:
            self.dlg = self.app.window(title=title)

    def _ensure(self):
        if self.app is None:
            raise ExecutionError("pywinauto app is not started. Call ui.open_app first.")

    def click(self, selector: str) -> None:
        self._ensure()
        # selector: best-effort: treat as 'best_match'
        (self.dlg or self.app).child_window(best_match=selector).click_input()

    def type(self, selector: str, text: str) -> None:
        self._ensure()
        ctrl = (self.dlg or self.app).child_window(best_match=selector)
        try:
            ctrl.set_edit_text(text)
        except Exception:
            ctrl.type_keys(text, with_spaces=True)

    def wait_for(self, selector: str, text_contains: Optional[str], timeout_ms: int) -> None:
        self._ensure()
        import time
        end = time.time() + timeout_ms / 1000.0
        while time.time() < end:
            try:
                ctrl = (self.dlg or self.app).child_window(best_match=selector)
                if text_contains is None:
                    if ctrl.exists():
                        return
                else:
                    if text_contains in (ctrl.window_text() or ""):
                        return
            except Exception:
                pass
            time.sleep(0.25)
        raise ExecutionError(f"wait_for timeout: {selector}")

    def get_text(self, selector: str) -> str:
        self._ensure()
        ctrl = (self.dlg or self.app).child_window(best_match=selector)
        return ctrl.window_text()

    def screenshot(self, path: str) -> None:
        self._ensure()
        try:
            (self.dlg or self.app).capture_as_image().save(path)
        except Exception as e:
            raise ExecutionError(f"pywinauto screenshot failed: {e}") from e

    def close(self) -> None:
        if self.app is None:
            return
        try:
            self.app.kill()
        except Exception:
            pass
        self.app = None
        self.dlg = None
