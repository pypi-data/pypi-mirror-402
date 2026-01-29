from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import ExecutionError
from .ui.base import UISettings, ensure_supported_backend
from .ui.selenium_driver import SeleniumUIDriver, SeleniumSettings
from .ui.appium_driver import AppiumUIDriver
from .ui.pywinauto_driver import PyWinAutoUIDriver
from .ui.agent_browser_driver import AgentBrowserUIDriver, AgentBrowserSettings

@dataclass
class UIContext:
    driver: Any  # UIDriver
    backend: str

def create_ui_driver(ui_cfg: Dict[str, Any], backend_override: Optional[str], backend_cfg: Dict[str, Any]) -> UIContext:
    ui = UISettings(
        backend=ensure_supported_backend(backend_override or ui_cfg.get("backend", "selenium")),
        headless=bool(ui_cfg.get("headless", True)),
        implicit_wait_ms=int(ui_cfg.get("implicit_wait_ms", 0) or 0),
    )
    if ui.backend == "selenium":
        def _as_list(value: Any) -> list[str]:
            if value is None:
                return []
            if isinstance(value, (list, tuple)):
                return [str(v) for v in value]
            return [str(value)]

        prefs = backend_cfg.get("prefs")
        selenium = SeleniumSettings(
            browser=str(backend_cfg.get("browser", "chrome")),
            driver_path=backend_cfg.get("driver_path"),
            browser_binary=backend_cfg.get("browser_binary"),
            args=_as_list(backend_cfg.get("args")),
            prefs=dict(prefs) if isinstance(prefs, dict) else {},
            user_data_dir=backend_cfg.get("user_data_dir"),
            download_dir=backend_cfg.get("download_dir"),
            window_size=backend_cfg.get("window_size"),
            page_load_timeout_ms=int(backend_cfg.get("page_load_timeout_ms", 0) or 0),
            script_timeout_ms=int(backend_cfg.get("script_timeout_ms", 0) or 0),
            auto_wait_ms=int(backend_cfg.get("auto_wait_ms", 0) or 0),
        )
        return UIContext(driver=SeleniumUIDriver(ui, selenium), backend="selenium")
    if ui.backend == "appium":
        return UIContext(driver=AppiumUIDriver(ui), backend="appium")
    if ui.backend == "pywinauto":
        return UIContext(driver=PyWinAutoUIDriver(ui), backend="pywinauto")
    if ui.backend == "agent-browser":
        def _as_list(value: Any) -> list[str]:
            if value is None:
                return []
            if isinstance(value, (list, tuple)):
                return [str(v) for v in value]
            return [str(value)]

        agent_browser = AgentBrowserSettings(
            binary=str(backend_cfg.get("binary", "agent-browser")),
            timeout_ms=int(backend_cfg.get("timeout_ms", 30000) or 30000),
            poll_ms=int(backend_cfg.get("poll_ms", 250) or 250),
            extra_args=_as_list(backend_cfg.get("extra_args")),
            wsl_fallback=bool(backend_cfg.get("wsl_fallback", False)),
            wsl_distro=backend_cfg.get("wsl_distro"),
            wsl_workdir=backend_cfg.get("wsl_workdir"),
        )
        return UIContext(driver=AgentBrowserUIDriver(ui, agent_browser), backend="agent-browser")
    raise ExecutionError(f"Unknown backend: {ui.backend}")


def _safe(s: str) -> str:
    import re
    s = (s or "").strip()
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s[:80] or "step"

def _forensics_dump(ctx, *, prefix: str) -> dict:
    """Best-effort diagnostics: screenshot + (selenium) url + page_source."""
    import time
    from pathlib import Path

    out: dict = {}
    ts = time.strftime("%Y%m%d-%H%M%S")
    case_id = _safe(str(getattr(ctx, "case", {}).get("id", "case")))
    step_key = _safe(prefix)
    base_dir = Path(getattr(ctx, "artifact_dir", "artifacts")) / "forensics"
    base_dir.mkdir(parents=True, exist_ok=True)

    # screenshot (all backends)
    shot = base_dir / f"{case_id}__{step_key}__{ts}.png"
    try:
        ctx.ui.driver.screenshot(str(shot))
        out["screenshot"] = str(shot)
    except Exception:
        pass

    # selenium extras
    drv = getattr(ctx.ui, "driver", None)
    # current_url
    try:
        url = getattr(drv, "driver", drv).current_url  # SeleniumUIDriver keeps .driver
        out["current_url"] = str(url)
    except Exception:
        pass
    # page_source
    try:
        src = getattr(getattr(drv, "driver", drv), "page_source")
        html = base_dir / f"{case_id}__{step_key}__{ts}.html"
        html.write_text(src, encoding="utf-8", errors="replace")
        out["page_source"] = str(html)
    except Exception:
        pass

    return out


def ui_open(ctx, step_args: Dict[str, Any]) -> None:
    ctx.ui.driver.open(step_args["url"])

def ui_open_app(ctx, step_args: Dict[str, Any]) -> None:
    server_url = step_args.get("server_url") or step_args.get("server")
    caps = step_args.get("caps") or {}
    if not server_url:
        raise ExecutionError("ui.open_app requires server_url")
    ctx.ui.driver.open_app(server_url, caps)

def ui_click(ctx, step_args: Dict[str, Any]) -> None:
    ctx.ui.driver.click(step_args["selector"])

def ui_type(ctx, step_args: Dict[str, Any]) -> None:
    ctx.ui.driver.type(step_args["selector"], str(step_args.get("text", "")))

def ui_wait_for(ctx, step_args: Dict[str, Any]) -> None:
    selector = step_args["selector"]
    text_contains = step_args.get("text_contains")
    timeout_ms = int(step_args.get("timeout_ms") or ctx.default_timeout_ms)
    try:
        ctx.ui.driver.wait_for(selector, text_contains, timeout_ms)
    except Exception as e:
        # Collect diagnostics to reduce debugging cost
        prefix = f"wait_for_{selector}"
        diag = _forensics_dump(ctx, prefix=prefix)

        msg = f"ui.wait_for failed: selector={selector!r} timeout_ms={timeout_ms}"
        if text_contains is not None:
            msg += f" text_contains={text_contains!r}"
        if diag.get("current_url"):
            msg += f" url={diag['current_url']}"
        if diag.get("screenshot"):
            msg += f" screenshot={diag['screenshot']}"
        if diag.get("page_source"):
            msg += f" page_source={diag['page_source']}"
        # preserve original exception type/message as tail
        raise ExecutionError(msg + f" ({e.__class__.__name__}: {e})") from e


def ui_get_text(ctx, step_args: Dict[str, Any]) -> str:
    return ctx.ui.driver.get_text(step_args["selector"])

def ui_screenshot(ctx, step_args: Dict[str, Any]) -> None:
    path = step_args.get("path")
    if not path:
        raise ExecutionError("ui.screenshot requires path")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    ctx.ui.driver.screenshot(path)

def ui_close(ctx, step_args: Dict[str, Any]) -> None:
    ctx.ui.driver.close()
