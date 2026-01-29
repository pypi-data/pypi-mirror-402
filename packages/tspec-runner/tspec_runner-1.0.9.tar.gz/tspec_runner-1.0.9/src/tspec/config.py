from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # py311+
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore

from .errors import ValidationError

@dataclass(frozen=True)
class RunnerConfig:
    ui: Dict[str, Any]
    selenium: Dict[str, Any]
    appium: Dict[str, Any]
    pywinauto: Dict[str, Any]
    agent_browser: Dict[str, Any]

def load_config(path: Optional[Path]) -> RunnerConfig:
    if path is None:
        return RunnerConfig(ui={}, selenium={}, appium={}, pywinauto={}, agent_browser={})
    if tomllib is None:
        raise ValidationError("tomllib is not available; use Python 3.11+")
    p = path.resolve()
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ValidationError(f"Config not found: {p}") from e
    except Exception as e:
        raise ValidationError(f"Failed to parse TOML: {p} ({e})") from e

    return RunnerConfig(
        ui=dict(data.get("ui", {})),
        selenium=dict(data.get("selenium", {})),
        appium=dict(data.get("appium", {})),
        pywinauto=dict(data.get("pywinauto", {})),
        agent_browser=dict(data.get("agent_browser", {})),
    )
