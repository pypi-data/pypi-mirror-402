from __future__ import annotations

import os
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

def check_android_env() -> list[Check]:
    checks: list[Check] = []
    sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    checks.append(Check("ANDROID_SDK_ROOT/ANDROID_HOME", bool(sdk), sdk or "not set"))

    adb = _which("adb")
    checks.append(Check("adb", bool(adb), adb or "not found in PATH"))
    emu = _which("emulator")
    checks.append(Check("emulator", bool(emu), emu or "not found in PATH"))

    if adb:
        try:
            out = subprocess.check_output(["adb", "devices"], text=True, stderr=subprocess.STDOUT)
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            devs = [ln for ln in lines[1:] if "\t" in ln]
            ok = len(devs) > 0
            detail = ", ".join(devs) if devs else "no devices (start emulator or connect device)"
            checks.append(Check("adb devices", ok, detail))
        except Exception as e:
            checks.append(Check("adb devices", False, str(e)))
    else:
        checks.append(Check("adb devices", False, "adb not available"))

    return checks
