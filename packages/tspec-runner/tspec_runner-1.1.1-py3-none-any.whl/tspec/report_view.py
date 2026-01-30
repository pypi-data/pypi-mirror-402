from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .errors import ValidationError

VALID_STATUSES = {"passed", "failed", "error", "skipped"}

def format_error_message(err: Any, *, full_trace: bool = False, max_len: int = 160) -> str:
    """Normalize noisy driver errors (e.g., Selenium stacktrace) into human-friendly text."""
    if err is None:
        return ""
    msg = ""
    if isinstance(err, dict):
        msg = str(err.get("message") or err.get("type") or "")
    else:
        msg = str(err)
    msg = msg.replace("\r\n", "\n")
    # Common Selenium formatting: "Message: ...\nStacktrace: ..."
    if not full_trace and "Stacktrace:" in msg:
        msg = msg.split("Stacktrace:", 1)[0]
    # Strip leading "Message:" label
    if msg.lstrip().startswith("Message:"):
        msg = msg.split("Message:", 1)[1]
    # Collapse whitespace
    msg = " ".join(msg.strip().split())
    if max_len and len(msg) > max_len:
        msg = msg[: max_len - 1] + "…"
    return msg

@dataclass(frozen=True)
class StepView:
    do: str
    name: Optional[str]
    status: str
    duration_ms: int
    error: Optional[Dict[str, Any]]

@dataclass(frozen=True)
class CaseView:
    id: str
    title: str
    status: str
    steps: List[StepView]

@dataclass(frozen=True)
class ReportView:
    suite: Dict[str, Any]
    cases: List[CaseView]

def load_report(path: Path) -> ReportView:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ValidationError(f"Report not found: {path}") from e
    except Exception as e:
        raise ValidationError(f"Failed to read report JSON: {path} ({e})") from e

    suite = raw.get("suite") or {}
    cases_in = raw.get("cases")
    if not isinstance(cases_in, list):
        raise ValidationError("Invalid report: missing 'cases' list")

    cases: List[CaseView] = []
    for c in cases_in:
        if not isinstance(c, dict):
            continue
        steps_in = c.get("steps") or []
        steps: List[StepView] = []
        if isinstance(steps_in, list):
            for s in steps_in:
                if not isinstance(s, dict):
                    continue
                steps.append(
                    StepView(
                        do=str(s.get("do", "")),
                        name=s.get("name"),
                        status=str(s.get("status", "")),
                        duration_ms=int(s.get("duration_ms") or 0),
                        error=s.get("error"),
                    )
                )
        cases.append(
            CaseView(
                id=str(c.get("id", "")),
                title=str(c.get("title", "")),
                status=str(c.get("status", "")),
                steps=steps,
            )
        )
    return ReportView(suite=suite, cases=cases)

def normalize_statuses(statuses: Optional[Sequence[str]]) -> Optional[set[str]]:
    if not statuses:
        return None
    out = set()
    for s in statuses:
        ss = (s or "").strip().lower()
        if not ss:
            continue
        if ss not in VALID_STATUSES:
            raise ValidationError(f"Unknown status filter: {s!r} (allowed: {sorted(VALID_STATUSES)})")
        out.add(ss)
    return out or None

def filter_cases(
    rep: ReportView,
    *,
    case_ids: Optional[Sequence[str]] = None,
    statuses: Optional[Sequence[str]] = None,
    grep: Optional[str] = None,
) -> List[CaseView]:
    want_statuses = normalize_statuses(statuses)
    want_ids = {c.strip() for c in (case_ids or []) if c and c.strip()}
    g = (grep or "").strip().lower()

    out: List[CaseView] = []
    for c in rep.cases:
        if want_ids and c.id not in want_ids:
            continue
        if want_statuses and c.status.lower() not in want_statuses:
            continue
        if g and (g not in c.id.lower()) and (g not in c.title.lower()):
            continue
        out.append(c)
    return out

def summarize_failures(
    cases: Iterable[CaseView],
    *,
    full_trace: bool = False,
    max_len: int = 160,
) -> List[Tuple[str, str, str, str]]:
    """Return (case_id, case_title, step_do, message) for first failing step per case."""
    rows: List[Tuple[str, str, str, str]] = []
    for c in cases:
        if c.status not in ("failed", "error"):
            continue
        step_do = "-"
        msg = ""
        for s in c.steps:
            if s.status in ("failed", "error"):
                step_do = s.do or "-"
                msg = format_error_message(s.error, full_trace=full_trace, max_len=max_len)
                break
        rows.append((c.id, c.title, step_do, msg))
    return rows
