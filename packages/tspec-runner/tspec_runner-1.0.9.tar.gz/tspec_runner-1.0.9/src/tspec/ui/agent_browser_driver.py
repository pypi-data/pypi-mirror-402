from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import platform
import shlex
import socket
import subprocess
import time
from typing import Any, Optional

from ..errors import ExecutionError
from .base import UISettings


@dataclass
class AgentBrowserSettings:
    binary: str = "agent-browser"
    timeout_ms: int = 30000
    poll_ms: int = 250
    extra_args: Optional[list[str]] = None
    wsl_fallback: bool = False
    wsl_distro: Optional[str] = None
    wsl_workdir: Optional[str] = None


def _windows_path_to_wsl(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        return path
    drive = p.drive.replace(":", "").lower()
    rest = str(p).replace("\\", "/").split(":", 1)[-1]
    return f"/mnt/{drive}{rest}"


def _resolve_windows_agent_browser(binary: str) -> Optional[str]:
    p = Path(binary)
    if p.is_file():
        return str(p)
    if p.suffix.lower() == ".exe" and p.exists():
        return str(p)
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    arch = platform.machine().lower()
    if arch in ("amd64", "x86_64"):
        arch = "x64"
    elif arch in ("aarch64", "arm64"):
        arch = "arm64"
    base = Path(appdata) / "npm" / "node_modules" / "agent-browser" / "bin"
    candidate = base / f"agent-browser-win32-{arch}.exe"
    if candidate.exists():
        return str(candidate)
    return None


def _get_daemon_paths(binary: str) -> tuple[Optional[Path], Optional[Path]]:
    try:
        base = Path(binary).resolve().parent.parent
        daemon = base / "dist" / "daemon.js"
        if daemon.exists():
            return base, daemon
    except Exception:
        pass
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None, None
    base = Path(appdata) / "npm" / "node_modules" / "agent-browser"
    daemon = base / "dist" / "daemon.js"
    if daemon.exists():
        return base, daemon
    return None, None


def _port_file(session: str) -> Path:
    tmp = Path(os.environ.get("TEMP", Path.cwd()))
    return tmp / f"agent-browser-{session}.port"


def _pid_file(session: str) -> Path:
    tmp = Path(os.environ.get("TEMP", Path.cwd()))
    return tmp / f"agent-browser-{session}.pid"


def _is_port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except Exception:
        return False


def _ensure_daemon_running(binary: str, session: str = "default", timeout_s: float = 5.0) -> int:
    port_path = _port_file(session)
    pid_path = _pid_file(session)
    if port_path.exists():
        try:
            port = int(port_path.read_text(encoding="utf-8").strip())
            if _is_port_open(port):
                return port
        except Exception:
            pass
    _base, daemon = _get_daemon_paths(binary)
    if not daemon:
        raise ExecutionError("agent-browser daemon script not found (dist/daemon.js).")
    creationflags = 0
    if os.name == "nt":
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
        creationflags |= getattr(subprocess, "DETACHED_PROCESS", 0)
    subprocess.Popen(
        ["node", str(daemon)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            if port_path.exists():
                port = int(port_path.read_text(encoding="utf-8").strip())
                if _is_port_open(port):
                    return port
        except Exception:
            pass
        time.sleep(0.1)
    raise ExecutionError("agent-browser daemon failed to start (protocol fallback).")


class AgentBrowserUIDriver:
    def __init__(self, ui: UISettings, settings: AgentBrowserSettings) -> None:
        self.ui = ui
        self.settings = settings
        self._use_wsl = False
        self._use_protocol = False
        self._seq = 0
        if os.name == "nt":
            resolved = _resolve_windows_agent_browser(self.settings.binary)
            if resolved:
                self.settings.binary = resolved

    def _build_cmd(self, *args: str) -> list[str]:
        cmd = [self.settings.binary]
        if self.settings.extra_args:
            cmd.extend(self.settings.extra_args)
        cmd.extend(args)
        return cmd

    def _run_local(self, cmd: list[str]) -> str:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.settings.timeout_ms / 1000.0,
                check=True,
            )
        except FileNotFoundError as e:
            raise e
        except subprocess.CalledProcessError as e:
            stderr = (e.stderr or "").strip()
            stdout = (e.stdout or "").strip()
            detail = stderr or stdout or str(e)
            detail = detail.encode("ascii", "replace").decode("ascii")
            raise ExecutionError(f"agent-browser failed: {' '.join(cmd)} ({detail})") from e
        return (proc.stdout or "").strip()

    def _run_wsl(self, cmd: list[str]) -> str:
        if os.name != "nt":
            raise ExecutionError("WSL fallback is only supported on Windows.")
        quoted = " ".join(shlex.quote(arg) for arg in cmd)
        if self.settings.wsl_workdir:
            quoted = f"cd {shlex.quote(self.settings.wsl_workdir)} && {quoted}"
        wsl_cmd = ["wsl.exe"]
        if self.settings.wsl_distro:
            wsl_cmd.extend(["-d", self.settings.wsl_distro])
        wsl_cmd.extend(["--", "bash", "-lc", quoted])
        try:
            proc = subprocess.run(
                wsl_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.settings.timeout_ms / 1000.0,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            stderr = (e.stderr or "").strip()
            stdout = (e.stdout or "").strip()
            detail = stderr or stdout or str(e)
            detail = detail.encode("ascii", "replace").decode("ascii")
            raise ExecutionError(f"agent-browser failed (wsl): {quoted} ({detail})") from e
        return (proc.stdout or "").strip()

    def _run(self, *args: str) -> str:
        cmd = self._build_cmd(*args)
        if self._use_wsl:
            return self._run_wsl(cmd)
        try:
            return self._run_local(cmd)
        except FileNotFoundError as e:
            if os.name == "nt" and self.settings.wsl_fallback:
                self._use_wsl = True
                return self._run_wsl(cmd)
            raise ExecutionError(
                "agent-browser CLI not found. Install with: npm install -g agent-browser"
            ) from e

    def open(self, url: str) -> None:
        try:
            self._run("open", url)
        except ExecutionError as e:
            if self._maybe_use_protocol(e):
                self._protocol_request({"action": "navigate", "url": url})
                return
            raise

    def open_app(self, server_url: str, caps: dict) -> None:
        raise ExecutionError("open_app is not supported on agent-browser backend.")

    def click(self, selector: str) -> None:
        try:
            self._run("click", selector)
        except ExecutionError as e:
            if self._maybe_use_protocol(e):
                self._protocol_request({"action": "click", "selector": selector})
                return
            raise

    def type(self, selector: str, text: str) -> None:
        try:
            self._run("type", selector, text)
        except ExecutionError as e:
            if self._maybe_use_protocol(e):
                self._protocol_request({"action": "type", "selector": selector, "text": text})
                return
            raise

    def wait_for(self, selector: str, text_contains: Optional[str], timeout_ms: int) -> None:
        deadline = time.monotonic() + (timeout_ms / 1000.0)
        last_error: Optional[str] = None
        while time.monotonic() < deadline:
            try:
                if self._use_protocol:
                    self._protocol_request({"action": "wait", "selector": selector, "timeout": timeout_ms, "state": "visible"})
                    if text_contains is None:
                        return
                    text = self._protocol_request({"action": "gettext", "selector": selector}).get("text", "")
                    if text_contains in text:
                        return
                    last_error = f"text_contains not matched: {text_contains!r}"
                else:
                    count = self._run("get", "count", selector)
                    if count.strip().isdigit() and int(count.strip()) > 0:
                        if text_contains is None:
                            return
                        text = self._run("get", "text", selector)
                        if text_contains in text:
                            return
                        last_error = f"text_contains not matched: {text_contains!r}"
                    else:
                        last_error = "selector not found"
            except ExecutionError as e:
                if self._maybe_use_protocol(e):
                    continue
                last_error = str(e)
            time.sleep(self.settings.poll_ms / 1000.0)
        raise ExecutionError(f"wait_for timed out: selector={selector!r} ({last_error})")

    def get_text(self, selector: str) -> str:
        try:
            return self._run("get", "text", selector)
        except ExecutionError as e:
            if self._maybe_use_protocol(e):
                return self._protocol_request({"action": "gettext", "selector": selector}).get("text", "")
            raise

    def screenshot(self, path: str) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            if self._use_wsl:
                self._run("screenshot", _windows_path_to_wsl(str(out)))
            else:
                self._run("screenshot", str(out))
        except ExecutionError as e:
            if self._maybe_use_protocol(e):
                self._protocol_request({"action": "screenshot", "path": str(out)})
                return
            raise

    def close(self) -> None:
        try:
            self._run("close")
        except ExecutionError as e:
            if self._maybe_use_protocol(e):
                self._protocol_request({"action": "close"})
                return
            raise

    def _maybe_use_protocol(self, err: ExecutionError) -> bool:
        msg = str(err)
        if "Daemon failed to start" not in msg and "daemon failed to start" not in msg:
            return False
        if not self._use_protocol and os.name == "nt":
            self._use_protocol = True
            return True
        return self._use_protocol

    def _protocol_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        port = _ensure_daemon_running(self.settings.binary)
        self._seq += 1
        payload = dict(payload)
        payload["id"] = str(self._seq)
        msg = json.dumps(payload) + "\n"
        with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
            s.sendall(msg.encode("utf-8"))
            s.settimeout(self.settings.timeout_ms / 1000.0)
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
        line = buf.decode("utf-8", errors="replace").strip()
        if not line:
            raise ExecutionError("agent-browser protocol: empty response")
        data = json.loads(line)
        if not data.get("success", False):
            msg = str(data.get("error") or data.get("message") or "unknown error")
            raise ExecutionError(f"agent-browser protocol error: {msg}")
        return data.get("data", {})
