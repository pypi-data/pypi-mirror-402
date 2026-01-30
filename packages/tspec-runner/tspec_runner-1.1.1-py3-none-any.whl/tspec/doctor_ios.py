from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str

def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
        return True, out
    except Exception as e:
        return False, str(e)

def check_ios_env() -> list[Check]:
    checks: list[Check] = []
    is_macos = platform.system().lower() == "darwin"
    checks.append(Check("platform", is_macos, platform.platform()))

    xcodebuild = _which("xcodebuild")
    checks.append(Check("xcodebuild", bool(xcodebuild), xcodebuild or "not found (install Xcode)"))
    xcrun = _which("xcrun")
    checks.append(Check("xcrun", bool(xcrun), xcrun or "not found (install Xcode CLT)"))

    if xcodebuild:
        ok, out = _run(["xcodebuild", "-version"])
        checks.append(Check("xcodebuild -version", ok, out))
    if xcrun:
        ok, out = _run(["xcrun", "simctl", "list", "devices"])
        # avoid huge output; show only first few lines
        short = "\n".join(out.splitlines()[:8]) if out else out
        checks.append(Check("xcrun simctl list devices", ok, short))

    # Environment variables often used
    dev_dir = os.environ.get("DEVELOPER_DIR")
    checks.append(Check("DEVELOPER_DIR", True, dev_dir or "(not set)"))

    return checks
