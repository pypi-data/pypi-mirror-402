from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

from .ui.selenium_utils import extract_major_version

@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str

def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def _first_in_path(candidates: list[str]) -> Optional[str]:
    for cmd in candidates:
        found = _which(cmd)
        if found:
            return found
    return None

def _run_version(cmd: str) -> Optional[str]:
    try:
        return subprocess.check_output([cmd, "--version"], text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return None

def check_selenium_env() -> list[Check]:
    checks: list[Check] = []

    # python module
    try:
        import selenium  # noqa: F401
        checks.append(Check("python: selenium", True, "import ok"))
    except Exception as e:
        checks.append(Check("python: selenium", False, f"import failed: {e} (install: pip install -e '.[selenium]')"))

    # drivers
    chromedriver = _which("chromedriver")
    checks.append(Check("chromedriver", bool(chromedriver), chromedriver or "not found in PATH"))
    geckodriver = _which("geckodriver")
    checks.append(Check("geckodriver", bool(geckodriver), geckodriver or "not found in PATH (optional)"))

    # browsers (best-effort; varies by OS)
    chrome = _first_in_path(["google-chrome", "chrome", "chromium", "chromium-browser"])
    checks.append(Check("chrome", bool(chrome), chrome or "not found in PATH (macOS app may still exist)"))
    firefox = _which("firefox")
    checks.append(Check("firefox", bool(firefox), firefox or "not found in PATH (optional)"))

    # versions (best-effort)
    chrome_version = _run_version(chrome) if chrome else None
    if chrome and chrome_version:
        checks.append(Check("chrome --version", True, chrome_version))
    elif chrome:
        checks.append(Check("chrome --version", False, "version check failed"))

    chromedriver_version = _run_version(chromedriver) if chromedriver else None
    if chromedriver:
        if chromedriver_version:
            checks.append(Check("chromedriver --version", True, chromedriver_version))
        else:
            checks.append(Check("chromedriver --version", False, "version check failed"))

    # major version match (Chrome vs ChromeDriver)
    if chrome_version and chromedriver_version:
        chrome_major = extract_major_version(chrome_version)
        driver_major = extract_major_version(chromedriver_version)
        if chrome_major and driver_major:
            ok = chrome_major == driver_major
            detail = f"chrome={chrome_major} chromedriver={driver_major}"
            if not ok:
                detail += " (mismatch)"
            checks.append(Check("chrome/chromedriver major", ok, detail))
    return checks
