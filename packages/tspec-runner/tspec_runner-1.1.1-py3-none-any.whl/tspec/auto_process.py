from __future__ import annotations

import atexit
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console

_AUTO_CONSOLE = Console()


@dataclass
class AutoProcess:
    label: str
    cmd: List[str]
    cwd: Optional[Path]
    proc: Optional[subprocess.Popen] = None


_auto_processes: List[AutoProcess] = []


def _start_auto_process(auto: AutoProcess) -> None:
    if auto.proc is not None:
        return
    _AUTO_CONSOLE.print(f"[blue]Starting auto process:[/blue] {auto.label} {' '.join(auto.cmd)}")
    auto.proc = subprocess.Popen(
        auto.cmd, cwd=str(auto.cwd) if auto.cwd else None, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    )
    _auto_processes.append(auto)


def _shutdown_auto_processes() -> None:
    for auto in _auto_processes:
        if auto.proc and auto.proc.poll() is None:
            try:
                auto.proc.terminate()
                for _ in range(10):
                    if auto.proc.poll() is not None:
                        break
                    time.sleep(0.1)
                else:
                    auto.proc.kill()
            except Exception:
                pass


atexit.register(_shutdown_auto_processes)


def resolve_uv_command(script_path: Optional[str], label: str, default: Optional[Path] = None) -> Optional[Tuple[List[str], Path]]:
    target = Path(script_path) if script_path else default
    if target is None:
        return None
    target = target.expanduser().resolve()
    if not target.exists():
        raise ValueError(f"{label} helper script not found at {target}")
    return (["uv", "run", "--with", "mcp", "python", str(target)], target.parent)


def launch_helper(label: str, script_path: Optional[str], default: Optional[Path] = None) -> None:
    resolved = resolve_uv_command(script_path, label, default)
    if resolved is None:
        return
    cmd, cwd = resolved
    _start_auto_process(AutoProcess(label, cmd, cwd))
