from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .config import load_config  # reuse config loader
from .context import RunContext
from .registry import build_registry
from .runner import Runner
from .validate import load_and_validate
from .actions_ui import create_ui_driver
from .errors import ExecutionError


def run_spec_file(
    target: Path,
    *,
    backend: Optional[str] = None,
    report: Optional[Path] = None,
    config: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run a spec file and optionally write report JSON.

    Returns the in-memory report dict (same structure as CLI).
    """
    doc, spec = load_and_validate(target)
    cfg = load_config(config)

    ctx = RunContext(
        vars=dict(doc.vars),
        env={},
        suite={"name": doc.suite.name, "tags": doc.suite.tags},
        default_timeout_ms=doc.suite.default_timeout_ms,
        artifact_dir=doc.suite.artifact_dir,
    )

    reg = build_registry()

    uses_ui = any((s.do or "").startswith("ui.") for c in doc.cases for s in c.steps)
    if uses_ui:
        ui_backend = backend or cfg.ui.get("backend", "selenium")
        backend_cfg = cfg.selenium if ui_backend == "selenium" else (cfg.appium if ui_backend == "appium" else (cfg.pywinauto if ui_backend == "pywinauto" else cfg.agent_browser))
        ctx.ui = create_ui_driver(cfg.ui, ui_backend, backend_cfg)

    runner = Runner(doc, ctx=ctx, registry=reg)
    result = runner.run()
    result["spec"] = {"resolved": str(spec.resolved), "declared": getattr(spec, "declared", None)}

    if report is not None:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return result
