from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .errors import ExecutionError
from .actions_ui import UIContext

@dataclass
class RunContext:
    vars: Dict[str, Any]
    env: Dict[str, Any]
    suite: Dict[str, Any]
    case: Dict[str, Any] = field(default_factory=dict)
    saved: Dict[str, Any] = field(default_factory=dict)

    # runtime settings
    default_timeout_ms: int = 15000

    artifact_dir: str = "artifacts"

    # optional subsystems
    ui: Optional[UIContext] = None

    def put_save(self, name: str, value: Any) -> None:
        self.saved[name] = value
        # also expose at top-level for `${name}` convenience
        self.__dict__[name] = value  # type: ignore[attr-defined]
