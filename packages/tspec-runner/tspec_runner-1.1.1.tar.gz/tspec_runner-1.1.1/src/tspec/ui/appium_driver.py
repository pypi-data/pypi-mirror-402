from __future__ import annotations

import time
from typing import Optional

from ..errors import ExecutionError
from .base import UIDriver, UISettings


class AppiumUIDriver(UIDriver):
    """Appium backend (Android/iOS) using Appium-Python-Client v4+ (W3C + Options API)."""

    def __init__(self, ui: UISettings):
        try:
            from appium import webdriver  # noqa: F401
            from appium.options.common import AppiumOptions  # noqa: F401
        except Exception as e:
            raise ExecutionError(
                "Appium backend selected but Appium-Python-Client is not installed. "
                "Install with: pip install -e '.[appium]'"
            ) from e

        self.driver = None
        self.ui = ui

    def open(self, url: str) -> None:
        raise ExecutionError("open(url) is not supported on appium backend. Use ui.open_app.")

    def open_app(self, server_url: str, caps: dict) -> None:
        """Start a session.

        `caps` is a plain dict from tspec. We convert it to AppiumOptions for v4+ compatibility.
        """
        from appium import webdriver
        from appium.options.common import AppiumOptions

        options = AppiumOptions()
        options.load_capabilities(caps or {})
        # Appium-Python-Client v4+: pass options=
        try:
            self.driver = webdriver.Remote(command_executor=server_url, options=options)
        except Exception as e:
            msg = str(e)
            # Common: Appium server not running / wrong URL
            if "Max retries exceeded with url: /session" in msg or "NewConnectionError" in msg:
                raise ExecutionError(f"Cannot reach Appium server at {server_url!r}. Start appium and confirm /status.") from e
            # Common: wrong appActivity
            if "Activity class" in msg and "does not exist" in msg:
                raise ExecutionError(
                    "Cannot start app: appActivity not found. "
                    "Run: adb shell cmd package resolve-activity --brief <appPackage> "
                    "and set appActivity to the returned value."
                ) from e
            raise ExecutionError(f"Appium session creation failed: {msg}") from e

        # Fast failure: ensure target app is in foreground (Android).
        try:
            platform = str((caps or {}).get("platformName", "")).lower()
            expected_pkg = (caps or {}).get("appium:appPackage") or (caps or {}).get("appPackage")
            if platform == "android" and expected_pkg:
                deadline = time.time() + 6.0
                last_pkg = None
                while time.time() < deadline:
                    try:
                        last_pkg = getattr(self.driver, "current_package", None)
                        if last_pkg == expected_pkg:
                            break
                    except Exception:
                        pass
                    time.sleep(0.25)
                if last_pkg != expected_pkg:
                    raise ExecutionError(f"App did not come to foreground: expected package={expected_pkg!r}, current={last_pkg!r}. Check appActivity/appWaitActivity or app crash.")
        except ExecutionError:
            # keep error
            raise
        except Exception:
            # never block session creation on this check
            pass

    def _ensure(self):
        if self.driver is None:
            raise ExecutionError("Appium driver is not started. Call ui.open_app first.")

    def _find(self, selector: str):
        """Selector convention:
        - aid=<id>      : accessibility id
        - id=<id>       : id (Android resource-id or iOS identifier depending on platform)
        - xpath=<expr>  : xpath
        - otherwise     : treated as xpath (legacy)
        """
        self._ensure()
        s = (selector or "").strip()
        if s.startswith("aid="):
            return self.driver.find_element("accessibility id", s[4:])
        if s.startswith("id="):
            return self.driver.find_element("id", s[3:])
        if s.startswith("xpath="):
            return self.driver.find_element("xpath", s[6:])
        return self.driver.find_element("xpath", s)

    def click(self, selector: str) -> None:
        el = self._find(selector)
        el.click()

    def type(self, selector: str, text: str) -> None:
        el = self._find(selector)
        try:
            el.clear()
        except Exception:
            pass
        el.send_keys(text)

    def wait_for(self, selector: str, text_contains: Optional[str], timeout_ms: int) -> None:
        self._ensure()
        end = time.time() + (timeout_ms / 1000.0)
        last_err: Optional[Exception] = None
        while time.time() < end:
            try:
                el = self._find(selector)
                if text_contains is None:
                    return
                if text_contains in (el.text or ""):
                    return
            except Exception as e:
                last_err = e
            time.sleep(0.25)
        raise ExecutionError(f"wait_for timeout: {selector} ({last_err})")

    def get_text(self, selector: str) -> str:
        el = self._find(selector)
        return el.text

    def screenshot(self, path: str) -> None:
        self._ensure()
        self.driver.get_screenshot_as_file(path)

    def close(self) -> None:
        if self.driver is None:
            return
        try:
            self.driver.quit()
        except Exception:
            pass
        self.driver = None
