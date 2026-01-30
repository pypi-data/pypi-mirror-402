from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from ..errors import ExecutionError
from .base import UISettings


@dataclass
class PlaywrightSettings:
    browser: str = "chromium"
    executable_path: Optional[str] = None
    args: Optional[list[str]] = None
    user_data_dir: Optional[str] = None
    window_size: Optional[str] = None
    timeout_ms: int = 30000
    allowlist_hosts: Optional[list[str]] = None


def _parse_window_size(value: Optional[str]) -> Optional[tuple[int, int]]:
    if not value:
        return None
    raw = str(value).strip().lower().replace(" ", "")
    if "x" not in raw:
        return None
    w, h = raw.split("x", 1)
    try:
        return int(w), int(h)
    except ValueError:
        return None


def _normalize_hosts(value: Optional[list[str]]) -> list[str]:
    if not value:
        return []
    out: list[str] = []
    for item in value:
        s = str(item or "").strip()
        if not s:
            continue
        out.append(s.lower())
    return out


class PlaywrightUIDriver:
    def __init__(self, ui: UISettings, settings: PlaywrightSettings) -> None:
        self.ui = ui
        self.settings = settings
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None

    def _ensure_page(self) -> None:
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ExecutionError("Playwright support requires: pip install -e '.[playwright]' and playwright install") from e

        self._pw = sync_playwright().start()
        browser_name = (self.settings.browser or "chromium").strip().lower()
        if not hasattr(self._pw, browser_name):
            raise ExecutionError(f"Unknown Playwright browser: {browser_name!r} (expected chromium|firefox|webkit)")
        browser_type = getattr(self._pw, browser_name)

        args = self.settings.args or []
        viewport = None
        size = _parse_window_size(self.settings.window_size)
        if size:
            viewport = {"width": size[0], "height": size[1]}

        if self.settings.user_data_dir:
            self._context = browser_type.launch_persistent_context(
                self.settings.user_data_dir,
                headless=self.ui.headless,
                args=args,
                executable_path=self.settings.executable_path,
                viewport=viewport,
            )
            if self._context.pages:
                self._page = self._context.pages[0]
            else:
                self._page = self._context.new_page()
        else:
            self._browser = browser_type.launch(
                headless=self.ui.headless,
                args=args,
                executable_path=self.settings.executable_path,
            )
            self._context = self._browser.new_context(viewport=viewport)
            self._page = self._context.new_page()

        timeout = int(self.settings.timeout_ms or 30000)
        if self._page:
            self._page.set_default_timeout(timeout)
            self._page.set_default_navigation_timeout(timeout)

    def _check_allowlist(self, url: str) -> None:
        allow = _normalize_hosts(self.settings.allowlist_hosts)
        if not allow:
            return
        host = urlparse(url).netloc.lower()
        if not host:
            raise ExecutionError(f"Invalid URL for playwright: {url!r}")
        host_only = host.split("@")[-1]
        if host_only in allow:
            return
        if ":" in host_only and host_only.split(":", 1)[0] in allow:
            return
        raise ExecutionError(f"Host not allowed for playwright: {host_only!r} (allowlist={allow})")

    def _locator(self, selector: str):
        if not self._page:
            raise ExecutionError("Playwright page is not initialized.")
        sel = (selector or "").strip()
        return self._page.locator(sel)

    def open(self, url: str) -> None:
        self._ensure_page()
        self._check_allowlist(url)
        self._page.goto(url, wait_until="load")

    def open_app(self, server_url: str, caps: dict) -> None:
        raise ExecutionError("open_app is not supported on Playwright backend.")

    def click(self, selector: str) -> None:
        loc = self._locator(selector)
        loc.first.click()

    def type(self, selector: str, text: str) -> None:
        loc = self._locator(selector)
        loc.first.fill(text)

    def wait_for(self, selector: str, text_contains: Optional[str], timeout_ms: int) -> None:
        loc = self._locator(selector)
        if text_contains:
            loc = loc.filter(has_text=text_contains)
        loc.first.wait_for(state="visible", timeout=timeout_ms)

    def get_text(self, selector: str) -> str:
        loc = self._locator(selector)
        return loc.first.inner_text()

    def screenshot(self, path: str) -> None:
        if not self._page:
            raise ExecutionError("Playwright page is not initialized.")
        self._page.screenshot(path=path)

    def close(self) -> None:
        try:
            if self._context:
                self._context.close()
        finally:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._pw = None
