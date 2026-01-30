#!/usr/bin/env python
"""Automated verification for `tspec run examples/assert_only.tspec.md --report out/report.json`. """

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], workdir: Path, env: dict[str, str]) -> int:
    print(f"Running: {' '.join(shlex.quote(part) for part in cmd)}")
    result = subprocess.run(cmd, cwd=workdir, env=env)
    print(f"Result: exit {result.returncode}")
    return result.returncode


def build_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    src_path = str(root / "src")
    if current_pythonpath:
        env["PYTHONPATH"] = os.pathsep.join([src_path, current_pythonpath])
    else:
        env["PYTHONPATH"] = src_path
    return env


def find_agent_browser() -> bool:
    if shutil.which("agent-browser"):
        return True
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidate = Path(appdata) / "npm" / "node_modules" / "agent-browser" / "bin" / "agent-browser-win32-x64.exe"
        if candidate.exists():
            return True
    return False


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    env = build_env(project_root)

    tspec_cmd = [
        sys.executable,
        "-m",
        "tspec.cli",
        "run",
        "examples/assert_only.tspec.md",
        "--report",
        "out/report.json",
    ]
    agent_browser_cmd = [
        sys.executable,
        "-m",
        "tspec.cli",
        "run",
        "examples/agent_browser_smoke.tspec.md",
        "--backend",
        "agent-browser",
        "--report",
        "out/agent-browser.json",
    ]
    pytest_cmd = [sys.executable, "-m", "pytest", "-q"]

    fail = False
    print("=== Auto verification: assert_only spec ===")
    if run_command(tspec_cmd, project_root, env) != 0:
        fail = True

    print("\n=== Auto verification: agent-browser smoke ===")
    if find_agent_browser():
        if run_command(agent_browser_cmd, project_root, env) != 0:
            fail = True
    else:
        print("agent-browser executable not detected; skipping test (install via `npm install -g agent-browser`).")

    print("\n=== Auto verification: pytest suite ===")
    if run_command(pytest_cmd, project_root, env) != 0:
        fail = True

    if fail:
        print("\nAuto verification failed.")
        sys.exit(1)
    print("\nAuto verification succeeded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
