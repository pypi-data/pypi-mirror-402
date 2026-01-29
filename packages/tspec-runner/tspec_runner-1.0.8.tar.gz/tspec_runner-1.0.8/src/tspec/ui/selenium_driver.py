from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..errors import ExecutionError
from .base import UIDriver, UISettings
from .selenium_utils import parse_selector, parse_window_size

@dataclass
class SeleniumSettings:
    browser: str = "chrome"  # chrome|firefox
    driver_path: Optional[str] = None
    browser_binary: Optional[str] = None
    args: list[str] = field(default_factory=list)
    prefs: dict[str, Any] = field(default_factory=dict)
    user_data_dir: Optional[str] = None
    download_dir: Optional[str] = None
    window_size: Optional[str] = None
    page_load_timeout_ms: Optional[int] = None
    script_timeout_ms: Optional[int] = None
    auto_wait_ms: int = 0

class SeleniumUIDriver(UIDriver):
    def __init__(self, ui: UISettings, selenium: SeleniumSettings):
        try:
            from selenium import webdriver  # noqa: F401
            from selenium.webdriver.common.by import By  # noqa: F401
        except Exception as e:
            raise ExecutionError(
                "Selenium backend selected but selenium is not installed. "
                "Install with: pip install -e '.[selenium]'"
            ) from e

        from selenium import webdriver

        browser = (selenium.browser or "chrome").lower()
        self._auto_wait_ms = selenium.auto_wait_ms or 0

        if browser == "chrome":
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            opts = Options()
            if selenium.browser_binary:
                opts.binary_location = selenium.browser_binary
            if ui.headless:
                opts.add_argument("--headless=new")
            if selenium.user_data_dir:
                opts.add_argument(f"--user-data-dir={selenium.user_data_dir}")
            for arg in selenium.args:
                opts.add_argument(arg)
            prefs = dict(selenium.prefs or {})
            if selenium.download_dir:
                prefs.setdefault("download.default_directory", str(selenium.download_dir))
            if prefs:
                opts.add_experimental_option("prefs", prefs)
            if selenium.driver_path:
                service = Service(executable_path=selenium.driver_path)
                self.driver = webdriver.Chrome(options=opts, service=service)
            else:
                self.driver = webdriver.Chrome(options=opts)
        elif browser == "firefox":
            from selenium.webdriver.firefox.options import Options
            from selenium.webdriver.firefox.service import Service
            opts = Options()
            if selenium.browser_binary:
                opts.binary_location = selenium.browser_binary
            if ui.headless:
                opts.add_argument("-headless")
            for arg in selenium.args:
                opts.add_argument(arg)
            if selenium.download_dir:
                opts.set_preference("browser.download.folderList", 2)
                opts.set_preference("browser.download.dir", str(selenium.download_dir))
            for key, value in (selenium.prefs or {}).items():
                opts.set_preference(key, value)
            if selenium.driver_path:
                service = Service(executable_path=selenium.driver_path)
                self.driver = webdriver.Firefox(options=opts, service=service)
            else:
                self.driver = webdriver.Firefox(options=opts)
        else:
            raise ExecutionError(f"Unsupported selenium browser: {selenium.browser!r}")

        if ui.implicit_wait_ms and ui.implicit_wait_ms > 0:
            self.driver.implicitly_wait(ui.implicit_wait_ms / 1000.0)
        if selenium.page_load_timeout_ms and selenium.page_load_timeout_ms > 0:
            self.driver.set_page_load_timeout(selenium.page_load_timeout_ms / 1000.0)
        if selenium.script_timeout_ms and selenium.script_timeout_ms > 0:
            self.driver.set_script_timeout(selenium.script_timeout_ms / 1000.0)
        if selenium.window_size:
            try:
                width_height = parse_window_size(selenium.window_size)
            except ValueError as e:
                raise ExecutionError(str(e)) from e
            if width_height:
                self.driver.set_window_size(*width_height)

    def _locate(self, selector: str) -> tuple[str, str]:
        try:
            return parse_selector(selector)
        except ValueError as e:
            raise ExecutionError(str(e)) from e

    def _find(self, selector: str, timeout_ms: int = 0, *, clickable: bool = False, visible: bool = False):
        by, value = self._locate(selector)
        if timeout_ms and timeout_ms > 0:
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
            except Exception:
                return self.driver.find_element(by, value)
            wait = WebDriverWait(self.driver, timeout_ms / 1000.0)
            if clickable:
                return wait.until(EC.element_to_be_clickable((by, value)))
            if visible:
                return wait.until(EC.visibility_of_element_located((by, value)))
            return wait.until(EC.presence_of_element_located((by, value)))
        return self.driver.find_element(by, value)

    def open(self, url: str) -> None:
        self.driver.get(url)

    def open_app(self, server_url: str, caps: dict) -> None:
        raise ExecutionError("open_app is not supported on selenium backend. Use appium backend.")

    def click(self, selector: str) -> None:
        el = self._find(selector, timeout_ms=self._auto_wait_ms, clickable=True)
        el.click()

    def type(self, selector: str, text: str) -> None:
        el = self._find(selector, timeout_ms=self._auto_wait_ms, visible=True)
        el.clear()
        el.send_keys(text)

    def wait_for(self, selector: str, text_contains: Optional[str], timeout_ms: int) -> None:
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except Exception as e:
            raise ExecutionError("Selenium support modules missing.") from e

        by, value = self._locate(selector)
        wait = WebDriverWait(self.driver, timeout_ms / 1000.0)
        if text_contains is None:
            wait.until(EC.presence_of_element_located((by, value)))
        else:
            wait.until(EC.text_to_be_present_in_element((by, value), text_contains))

    def get_text(self, selector: str) -> str:
        # Special case: 'title' selector returns document title (useful in demos)
        if selector.strip().lower() == "title":
            return self.driver.title
        el = self._find(selector, timeout_ms=self._auto_wait_ms)
        return el.text

    def screenshot(self, path: str) -> None:
        self.driver.save_screenshot(path)

    def close(self) -> None:
        try:
            self.driver.quit()
        except Exception:
            pass
