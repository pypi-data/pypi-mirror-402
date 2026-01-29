from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .errors import ExecutionError, ValidationError, SkipCaseError, StepTimeoutError
from .model import Document, Step
from .templating import render
from .when_expr import eval_when
from .registry import ActionRegistry
from .context import RunContext
from . import actions_assert
from . import actions_ui


@dataclass
class StepResult:
    do: str
    name: Optional[str]
    status: str
    duration_ms: int
    error: Optional[Dict[str, Any]] = None
    abort_case: bool = False
    skip_case: bool = False


class Runner:
    def __init__(self, doc: Document, *, ctx: RunContext, registry: ActionRegistry):
        self.doc = doc
        self.ctx = ctx
        self.registry = registry

    def _emit(self, kind: str, payload: Dict[str, Any]) -> None:
        """Emit a live event for --watch and forensics.

        - Stored into ctx.env['__events'] (report can optionally include this)
        - If ctx.env['__watch'] is true, prints a lightweight line
        """
        try:
            events = self.ctx.env.setdefault("__events", [])
            events.append({"ts": int(time.time() * 1000), "kind": kind, **payload})
        except Exception:
            pass

        if self.ctx.env.get("__watch"):
            msg = payload.get("msg") or payload.get("message") or ""
            print(f"[tspec][{kind}] {msg}")

    def _should_skip(self, skip_field) -> Tuple[bool, Optional[str]]:
        if skip_field is True:
            return True, "skipped"
        if isinstance(skip_field, str) and skip_field.strip():
            return True, skip_field.strip()
        return False, None

    def _when_ok(self, when_expr: Optional[str]) -> bool:
        if not when_expr:
            return True
        return eval_when(when_expr, self._render_ctx())

    def _render_ctx(self) -> Dict[str, Any]:
        # templating context; expose vars + saved at top-level
        base = {
            "vars": self.ctx.vars,
            "env": self.ctx.env,
            "suite": self.ctx.suite,
            "case": self.ctx.case,
            **self.ctx.vars,
            **self.ctx.saved,
        }
        return base

    def _dispatch(self, do: str, args: Dict[str, Any]) -> Any:
        if do not in self.registry.actions:
            raise ExecutionError(f"Unknown action: {do}")
        return self.registry.actions[do](self.ctx, args)

    def _effective_timeout_ms(self, step: Step) -> int:
        # step timeout overrides; else case timeout; else suite default
        case_to = None
        if isinstance(self.ctx.case, dict):
            case_to = self.ctx.case.get("timeout_ms")
        if step.timeout_ms is not None:
            return int(step.timeout_ms)
        if case_to is not None:
            return int(case_to)
        return int(self.doc.suite.default_timeout_ms)

    def _effective_retry(self, step: Step):
        return step.retry or self.doc.suite.default_retry

    def _effective_on_error(self, step: Step) -> Dict[str, Any]:
        oe = getattr(step, "on_error", None) or getattr(self.doc.suite, "default_on_error", None)
        if oe is None:
            return {"action": "abort", "note": ""}
        return {"action": getattr(oe, "action", "abort"), "note": getattr(oe, "note", "")}

    def _dispatch_with_timeout(self, action: str, args: Dict[str, Any], timeout_ms: int) -> Any:
        """Run a single action with a runner-side hard timeout."""
        def _call():
            return self._dispatch(action, args)

        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_call)
            try:
                return fut.result(timeout=timeout_ms / 1000.0)
            except FutureTimeoutError as e:
                raise StepTimeoutError(f"Step timed out after {timeout_ms}ms: {action}") from e

    def _run_step(self, step: Step, step_index: int) -> StepResult:
        # expose step index for diagnostics
        self.ctx.env["__step_index"] = step_index

        sk, reason = self._should_skip(step.skip)
        if sk:
            return StepResult(step.do, step.name, "skipped", 0, {"message": reason})

        if step.when and not self._when_ok(step.when):
            return StepResult(step.do, step.name, "skipped", 0, {"message": "when=false"})

        start = time.time()
        timeout_ms = self._effective_timeout_ms(step)
        retry = self._effective_retry(step)
        on_error = self._effective_on_error(step)

        # render args early (templating failure should be immediate)
        try:
            args = render(step.with_, self._render_ctx())
        except Exception as e:
            dur = int((time.time() - start) * 1000)
            err = {"type": e.__class__.__name__, "message": str(e), "on_error": on_error}
            self._emit("step_error", {"msg": f"{step.do} template error: {err['message']}", "do": step.do, "name": step.name})
            return StepResult(step.do, step.name, "error", dur, err, abort_case=True)

        # allow per-step timeout injection for ui.wait_for
        if step.timeout_ms is not None:
            args = dict(args)
            args.setdefault("timeout_ms", step.timeout_ms)

        attempts = 1 + (int(getattr(retry, "max", 0) or 0) if retry is not None else 0)
        backoff_ms = int(getattr(retry, "backoff_ms", 0) or 0) if retry is not None else 0

        self._emit("step_start", {"msg": f"{step.do} start (timeout={timeout_ms}ms, attempts={attempts})", "do": step.do, "name": step.name})

        last_exc: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                out = self._dispatch_with_timeout(step.do, args, timeout_ms)

                if isinstance(step.save, str) and step.save.strip():
                    self.ctx.put_save(step.save.strip(), out)

                dur = int((time.time() - start) * 1000)
                self._emit("step_end", {"msg": f"{step.do} passed ({dur}ms)", "do": step.do, "name": step.name})
                return StepResult(step.do, step.name, "passed", dur, None)

            except SkipCaseError as e:
                last_exc = e
                break
            except (StepTimeoutError, ExecutionError) as e:
                last_exc = e
            except Exception as e:
                last_exc = e

            if attempt < attempts:
                self._emit("step_retry", {"msg": f"{step.do} retry {attempt}/{attempts} after error: {last_exc}", "do": step.do, "name": step.name})
                if backoff_ms > 0:
                    time.sleep(backoff_ms / 1000.0)
                continue

        # final failure / or skip requested
        dur = int((time.time() - start) * 1000)
        etype = last_exc.__class__.__name__ if last_exc else "Error"
        emsg = str(last_exc) if last_exc else "unknown error"
        err: Dict[str, Any] = {"type": etype, "message": emsg, "on_error": on_error}

        action = (on_error.get("action") or "abort").lower()

        if action == "continue":
            self._emit("step_error", {"msg": f"{step.do} error but continue: {emsg}", "do": step.do, "name": step.name})
            return StepResult(step.do, step.name, "error", dur, err, abort_case=False)

        if action == "skip_case":
            self._emit("step_error", {"msg": f"{step.do} error -> skip_case: {emsg}", "do": step.do, "name": step.name})
            return StepResult(step.do, step.name, "skipped", dur, err, abort_case=True, skip_case=True)

        # abort (default)
        status = "failed" if isinstance(last_exc, ExecutionError) else "error"
        self._emit("step_error", {"msg": f"{step.do} {status}: {emsg}", "do": step.do, "name": step.name})
        return StepResult(step.do, step.name, status, dur, err, abort_case=True)

    def run(self) -> Dict[str, Any]:
        case_results = []

        for case in self.doc.cases:
            self.ctx.case = {"id": case.id, "title": case.title, "tags": case.tags, "timeout_ms": case.timeout_ms or None}

            sk, _reason = self._should_skip(case.skip)
            if sk or (case.when and not self._when_ok(case.when)):
                case_results.append({"id": case.id, "title": case.title, "status": "skipped", "steps": []})
                continue

            steps_out: List[Dict[str, Any]] = []
            status = "passed"

            for i, step in enumerate(case.steps, start=1):
                r = self._run_step(step, i)
                steps_out.append({
                    "do": r.do, "name": r.name, "status": r.status,
                    "duration_ms": r.duration_ms, "error": r.error,
                })

                # aggregate status (keep worst)
                if r.status in ("failed", "error"):
                    status = r.status
                elif r.status == "skipped" and r.skip_case:
                    status = "skipped"

                # stop current case if policy says so
                if r.abort_case:
                    break

                # suite-level fail_fast
                if self.doc.suite.fail_fast and status != "passed":
                    break

            case_results.append({"id": case.id, "title": case.title, "status": status, "steps": steps_out})
            if self.doc.suite.fail_fast and status != "passed":
                break

        out: Dict[str, Any] = {"suite": {"name": self.doc.suite.name, "tags": self.doc.suite.tags}, "cases": case_results}
        # include events if enabled/used
        if self.ctx.env.get("__events"):
            out["events"] = self.ctx.env["__events"]
        return out


def build_registry() -> ActionRegistry:
    reg = ActionRegistry()
    reg.register("assert.equals", lambda ctx, a: actions_assert.equals(a))
    reg.register("assert.true", lambda ctx, a: actions_assert.true(a))
    reg.register("assert.contains", lambda ctx, a: actions_assert.contains(a))
    reg.register("assert.matches", lambda ctx, a: actions_assert.matches(a))

    # ui.* actions depend on ctx.ui
    reg.register("ui.open", lambda ctx, a: actions_ui.ui_open(ctx, a))
    reg.register("ui.open_app", lambda ctx, a: actions_ui.ui_open_app(ctx, a))
    reg.register("ui.click", lambda ctx, a: actions_ui.ui_click(ctx, a))
    reg.register("ui.type", lambda ctx, a: actions_ui.ui_type(ctx, a))
    reg.register("ui.wait_for", lambda ctx, a: actions_ui.ui_wait_for(ctx, a))
    reg.register("ui.get_text", lambda ctx, a: actions_ui.ui_get_text(ctx, a))
    reg.register("ui.screenshot", lambda ctx, a: actions_ui.ui_screenshot(ctx, a))
    reg.register("ui.close", lambda ctx, a: actions_ui.ui_close(ctx, a))
    return reg
