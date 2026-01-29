from __future__ import annotations
import builtins
import os

import json
import re
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from .errors import ParseError, SpecVersionError, ValidationError, ExecutionError, TSpecError
from .validate import load_and_validate
from .spec_versions import SUPPORTED_SPECS, supported_window
from .config import load_config
from .context import RunContext
from .model import OnError
from .runner import Runner, build_registry
from .actions_ui import create_ui_driver
from .manual_loader import discover_manuals, find_manual_by_id, load_manual, manual_lang_from_path
from .doctor_android import check_android_env
from .doctor_selenium import check_selenium_env
from .doctor_ios import check_ios_env
from .mcp_server import start as mcp_start
from .assets import list_assets, extract_asset
from .pytest_reporting import generate_pytest_reports
from .report_view import load_report, filter_cases, summarize_failures, format_error_message
from .tspec_z1 import decode_z1_file, decompile_z1_file, expand_z1_sections, Z1Doc


def _coerce_opt_str(v):
    """Typer may return a list if an option is repeated; normalize to last value."""
    if v is None:
        return None
    try:
        import builtins as _b
        while isinstance(v, (_b.list, _b.tuple)) and v:
            v = v[-1]
    except Exception:
        pass
    return v
app = typer.Typer(add_completion=False, help="TSpec runner\nMarkdown + ```tspec blocks.")
manual_app = typer.Typer(add_completion=False, help="Environment / ops manuals (tspec-backed).")
app.add_typer(manual_app, name="manual")
console = Console()

def _exit(code: int, msg: Optional[str] = None):
    if msg:
        console.print(msg)
    raise typer.Exit(code)

def _z1_doc_to_dict(doc: Z1Doc) -> dict:
    return {
        "dictionary": dict(doc.dictionary),
        "sections": [{"tag": s.tag, "body": s.body} for s in doc.sections],
    }

def _z1_print(format: str, payload: dict | str) -> None:
    fmt = (format or "text").strip().lower()
    if fmt == "text":
        console.print(payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if fmt == "json":
        console.print_json(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if fmt == "yaml":
        try:
            import yaml
        except Exception as e:
            raise ExecutionError(f"YAML output requires PyYAML: {e}") from e
        console.print(yaml.safe_dump(payload, allow_unicode=False, sort_keys=False).rstrip())
        return
    raise ExecutionError(f"Unknown format: {format!r} (expected text|json|yaml)")


def _z1_doc_to_text(doc: Z1Doc) -> str:
    lines = ["TSPEC-Z1 DECODED", "DICT:"]
    if doc.dictionary:
        for key, value in doc.dictionary.items():
            lines.append(f"  {key}={value}")
    else:
        lines.append("  (empty)")
    lines.append("SECTIONS:")
    if doc.sections:
        for sec in doc.sections:
            lines.append(f"[{sec.tag}]")
            lines.append(sec.body)
    else:
        lines.append("  (empty)")
    return "\n".join(lines).rstrip()

def _short_error(err, max_len: int = 160):
    try:
        return format_error_message(err, full_trace=False, max_len=max_len)
    except Exception:
        s = str(err or '')
        s = ' '.join(s.strip().split())
        if max_len and len(s) > max_len:
            s = s[: max_len - 1] + '…'
        return s

@app.command()
def spec(
    android: bool = typer.Option(False, "--android", help="Run Android/Appium environment checks"),
    selenium: bool = typer.Option(False, "--selenium", help="Run Selenium/ChromeDriver environment checks"),
    ios: bool = typer.Option(False, "--ios", help="Run iOS/Xcode/XCUITest environment checks"),
):
    """Show runner spec support window."""
    g_min, g_latest, latest = supported_window(SUPPORTED_SPECS)
    table = Table(title="Spec support")
    table.add_column("latest")
    table.add_column("supported generations")
    table.add_column("supported versions")
    table.add_row(str(latest), f"{g_min}..{g_latest}", ", ".join(str(v) for v in SUPPORTED_SPECS))
    console.print(table)


    if android:
        at = Table(title="Android/Appium checks")
        at.add_column("check")
        at.add_column("status")
        at.add_column("detail")
        ok_all = True
        for c in check_android_env():
            at.add_row(c.name, "OK" if c.ok else "NG", c.detail)
            ok_all = ok_all and c.ok
        console.print(at)
        if not ok_all:
            console.print("Hint: tspec manual show android-env --full")



    if selenium:
        st = Table(title="Selenium/ChromeDriver checks")
        st.add_column("check")
        st.add_column("status")
        st.add_column("detail")
        ok_all = True
        for c in check_selenium_env():
            st.add_row(c.name, "OK" if c.ok else "NG", c.detail)
            ok_all = ok_all and c.ok
        console.print(st)
        if not ok_all:
            console.print("Hint: tspec manual show selenium-env --full")



    if ios:
        it = Table(title="iOS/Xcode/XCUITest checks")
        it.add_column("check")
        it.add_column("status")
        it.add_column("detail")
        ok_all = True
        for c in check_ios_env():
            it.add_row(c.name, "OK" if c.ok else "NG", c.detail)
            ok_all = ok_all and c.ok
        console.print(it)
        if not ok_all:
            console.print("Hint: tspec manual show ios-env --full")


@app.command()
def doctor(
    android: bool = typer.Option(False, "--android", help="Run Android/Appium environment checks"),
    selenium: bool = typer.Option(False, "--selenium", help="Run Selenium/ChromeDriver environment checks"),
    ios: bool = typer.Option(False, "--ios", help="Run iOS/Xcode/XCUITest environment checks"),
):
    """Check optional backends availability."""
    rows = []
    for name, mod, extra in [
        ("selenium", "selenium", ".[selenium]"),
        ("appium", "appium", ".[appium]"),
        ("pywinauto", "pywinauto", ".[pywinauto]"),
    ]:
        try:
            __import__(mod)
            rows.append((name, "OK", ""))
        except Exception as e:
            rows.append((name, "MISSING", f"pip install -e '{extra}'"))
    table = Table(title="Backend doctor")
    table.add_column("backend")
    table.add_column("status")
    table.add_column("install")
    for r in rows:
        table.add_row(*r)
    console.print(table)

@app.command()
def init(path: str = typer.Argument("example.tspec.md", help="Output path")):
    """Create a starter .tspec.md template."""
    from .templates import INIT_TEMPLATE
    p = Path(path)
    p.write_text(INIT_TEMPLATE, encoding="utf-8")
    console.print(f"Wrote {p}")


@manual_app.command("list")
def manual_list(
    base: Path = typer.Option(Path("docs"), "--base", help="Manual directory (default: docs)"),
    lang: Optional[str] = typer.Option(None, "--lang", help="Filter manuals by language (en|jp)"),
):
    """List available manuals."""
    lang = lang or os.environ.get("TSPEC_MANUAL_LANG")
    items = discover_manuals(base, lang=lang)
    table = Table(title=f"Manuals under {base}")
    table.add_column("id", no_wrap=True)
    table.add_column("lang", no_wrap=True)
    table.add_column("title")
    table.add_column("tags")
    table.add_column("path")
    for p, mf in items:
        table.add_row(mf.manual.id, manual_lang_from_path(p) or "-", mf.manual.title, ",".join(mf.manual.tags), str(p))
    console.print(table)
    _exit(0)

@manual_app.command("show")
def manual_show(
    target: str = typer.Argument(..., help="Manual id (e.g. android-env) or path"),
    base: Path = typer.Option(Path("docs"), "--base", help="Manual directory for id lookup"),
    full: bool = typer.Option(False, "--full", help="Show troubleshooting & references"),
    lang: Optional[str] = typer.Option(None, "--lang", help="Manual language (en|jp)"),
):
    """Show a manual on screen."""
    lang = lang or os.environ.get("TSPEC_MANUAL_LANG")
    p = Path(target)
    if p.exists():
        mf = load_manual(p)
    else:
        _p, mf = find_manual_by_id(base, target, lang=lang)
    man = mf.manual

    console.print(f"[bold]{man.title}[/bold]  (id={man.id})")
    if man.summary.strip():
        console.print(man.summary.strip())

    if man.prerequisites:
        t = Table(title="Prerequisites")
        t.add_column("item")
        for x in man.prerequisites:
            t.add_row(x)
        console.print(t)

    st = Table(title="Steps")
    st.add_column("#", no_wrap=True)
    st.add_column("title")
    st.add_column("body")
    for i, s in enumerate(man.steps, start=1):
        st.add_row(str(i), s.title, s.body.strip())
    console.print(st)

    if full and man.troubleshooting:
        tt = Table(title="Troubleshooting")
        tt.add_column("topic")
        tt.add_column("hint")
        for s in man.troubleshooting:
            tt.add_row(s.title, s.body.strip())
        console.print(tt)

    if full and man.references:
        rt = Table(title="References")
        rt.add_column("url")
        for r in man.references:
            rt.add_row(r)
        console.print(rt)

    _exit(0)

@app.command("z1-decode")
def z1_decode(
    path: Path = typer.Argument(..., help="Path to a .tspecz1 file"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text|json|yaml"),
):
    """Decode TSPEC-Z1 into structured sections."""
    try:
        doc = decode_z1_file(path)
        fmt = (format or "text").strip().lower()
        if fmt == "text":
            _z1_print(format, _z1_doc_to_text(doc))
        else:
            _z1_print(format, _z1_doc_to_dict(doc))
        _exit(0)
    except Exception as e:
        _exit(3, f"ERROR: {e}")


@app.command("z1-decompile")
def z1_decompile(
    path: Path = typer.Argument(..., help="Path to a .tspecz1 file"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text|json|yaml"),
):
    """Decompile TSPEC-Z1 into a human-readable expanded text."""
    try:
        text = decompile_z1_file(path)
        fmt = (format or "text").strip().lower()
        if fmt == "text":
            _z1_print(format, text)
            _exit(0)
        # For json/yaml, include expanded sections for machine use
        doc = decode_z1_file(path)
        expanded = expand_z1_sections(doc)
        payload = {
            "text": text,
            "dictionary": dict(doc.dictionary),
            "sections": [{"tag": s.tag, "body": s.body} for s in expanded],
        }
        _z1_print(format, payload)
        _exit(0)
    except Exception as e:
        _exit(3, f"ERROR: {e}")

@app.command()
def validate(
    target: str = typer.Argument(..., help=".tspec.md file"),
    explain_version: bool = typer.Option(False, "--explain-version", help="Print spec resolution details"),
):
    """Validate a .tspec.md file."""
    try:
        _doc, spec = load_and_validate(Path(target))
        if explain_version:
            console.print(f"spec.declared: {spec.declared!r}")
            console.print(f"spec.resolved: {spec.resolved}")
            console.print(f"reason: {spec.reason}")
        console.print("OK")
        _exit(0)
    except (ParseError, SpecVersionError, ValidationError) as e:
        _exit(2, f"ERROR: {e}")

@app.command()
def list(target: str = typer.Argument(..., help="File or directory")):
    """List cases."""
    p = Path(target)
    files: List[Path] = sorted(p.rglob("*.tspec.md")) if p.is_dir() else [p]
    if not files:
        _exit(2, "No .tspec.md found")

    table = Table(title="TSpec cases")
    table.add_column("file")
    table.add_column("id")
    table.add_column("title")
    table.add_column("tags")

    had_error = False
    for f in files:
        try:
            doc, _spec = load_and_validate(f)
            for c in doc.cases:
                table.add_row(str(f), c.id, c.title, ",".join(c.tags))
        except TSpecError as e:
            had_error = True
            table.add_row(str(f), "-", f"ERROR: {e}", "")
    console.print(table)
    _exit(2 if had_error else 0)


@app.command()
def report(
    path: str = typer.Argument(..., help="JSON report path (generated by tspec run --report)"),
    case: List[str] = typer.Option(None, "--case", "-c", help="Filter by case id (repeatable)"),
    status: List[str] = typer.Option(None, "--status", "-s", help="Filter by status (repeatable): passed|failed|error|skipped"),
    grep: Optional[str] = typer.Option(None, "--grep", "-g", help="Substring match on case id/title"),
    show_steps: bool = typer.Option(False, "--show-steps", help="Show steps table per case"),
    only_errors: bool = typer.Option(False, "--only-errors", help="Shortcut for --status failed --status error"),
    json_out: bool = typer.Option(False, "--json", help="Print filtered report JSON instead of tables"),
    full_trace: bool = typer.Option(False, "--full-trace", help="Do not strip/shorten stacktraces in messages"),
    max_message_len: int = typer.Option(160, "--max-message-len", help="Truncate error message length (0 = no limit)"),
):
    """Pretty-print a JSON report on screen (filters supported)."""
    try:
        rep = load_report(Path(path))
        statuses = status
        if only_errors:
            statuses = ["failed", "error"]

        cases = filter_cases(rep, case_ids=case, statuses=statuses, grep=grep)

        if json_out:
            out = {
                "suite": rep.suite,
                "cases": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "status": c.status,
                        "steps": [
                            {
                                "do": s.do,
                                "name": s.name,
                                "status": s.status,
                                "duration_ms": s.duration_ms,
                                "error": s.error,
                            }
                            for s in c.steps
                        ],
                    }
                    for c in cases
                ],
            }
            console.print(json.dumps(out, ensure_ascii=False, indent=2))
            _exit(0)

        title = rep.suite.get("name") or "Report"
        table = Table(title=f"Report: {title}")
        table.add_column("id", no_wrap=True)
        table.add_column("status")
        table.add_column("title")
        table.add_column("steps")
        table.add_column("duration(ms)")

        for c in cases:
            dur = sum(s.duration_ms for s in c.steps)
            table.add_row(c.id, c.status, c.title, str(len(c.steps)), str(dur))

        console.print(table)

        if show_steps:
            for c in cases:
                st = Table(title=f"Steps: {c.id} {c.title} ({c.status})")
                st.add_column("#", no_wrap=True)
                st.add_column("status")
                st.add_column("do")
                st.add_column("name")
                st.add_column("duration(ms)")
                st.add_column("error")
                for i, s in enumerate(c.steps, start=1):
                    err = format_error_message(s.error, full_trace=full_trace, max_len=max_message_len)
                st.add_row(str(i), s.status, s.do, str(s.name or ""), str(s.duration_ms), err)
                console.print(st)

        # If errors exist, show a compact failure summary at the end
        fail_rows = summarize_failures(cases, full_trace=full_trace, max_len=max_message_len)
        if fail_rows:
            ft = Table(title="Failure summary (first failing step per case)")
            ft.add_column("case_id", no_wrap=True)
            ft.add_column("title")
            ft.add_column("step")
            ft.add_column("message")
            for cid, title, step_do, msg in fail_rows:
                ft.add_row(cid, title, step_do, str(msg or ""))
            console.print(ft)

        _exit(0)

    except (ValidationError,) as e:
        _exit(2, f"ERROR: {e}")

@app.command()
def run(
    target: str = typer.Argument(..., help=".tspec.md file"),
    report: Optional[str] = typer.Option(None, "--report", help="Write JSON report to path"),
    backend: Optional[str] = typer.Option(None, "--backend", help="ui backend: selenium|appium|pywinauto|agent-browser"),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to tspec.toml"),
    watch: bool = typer.Option(False, "--watch/--no-watch", help="Live step progress logs"),
    step_timeout_ms: Optional[int] = typer.Option(None, "--step-timeout-ms", help="Override suite default hard step timeout (ms)"),
    pytest_html: Optional[str] = typer.Option(None, "--pytest-html", help="Write pytest-html report (requires extras: report)"),
    pytest_junitxml: Optional[str] = typer.Option(None, "--pytest-junitxml", help="Write pytest junitxml (requires extras: report)"),
    pytest_arg: List[str] = typer.Option([], "--pytest-arg", help="Extra arg passed to pytest (repeatable)"),
    on_error: str = typer.Option("abort", "--on-error", help="Default error policy: abort|skip_case|continue"),
):
    """Run cases. ui.* requires a backend."""
    try:
        doc, spec = load_and_validate(Path(target))
        cfg = load_config(config)

        ctx = RunContext(
            vars=dict(doc.vars),
            env={},
            suite={"name": doc.suite.name, "tags": doc.suite.tags},
            default_timeout_ms=doc.suite.default_timeout_ms,
            artifact_dir=doc.suite.artifact_dir,
        )

        # Initialize ui backend lazily if any ui.* action exists
        uses_ui = any(s.do.startswith("ui.") for c in doc.cases for s in c.steps)
        if uses_ui:
            ui_backend = backend or cfg.ui.get("backend", "selenium")
            # pick backend-specific config table
            backend_cfg = cfg.selenium if ui_backend == "selenium" else (cfg.appium if ui_backend == "appium" else (cfg.pywinauto if ui_backend == "pywinauto" else cfg.agent_browser))
            ctx.ui = create_ui_driver(cfg.ui, backend, backend_cfg)

        # live watch logs
        ctx.env["__watch"] = bool(watch)

        # override suite-level hard timeout if provided
        if step_timeout_ms is not None:
            doc.suite.default_timeout_ms = int(step_timeout_ms)

        # set default error policy
        if on_error:
            oe = on_error.strip().lower()
            if oe not in ("abort", "skip_case", "continue"):
                raise ExecutionError(f"Invalid --on-error: {on_error!r} (expected abort|skip_case|continue)")
            doc.suite.default_on_error = OnError(action=oe)

        reg = build_registry()
        runner = Runner(doc, ctx=ctx, registry=reg)

        console.print(f"Spec resolved: {spec.resolved}")
        if uses_ui:
            console.print(f"UI backend: {ctx.ui.backend}")

        result = runner.run()

        passed = sum(1 for c in result["cases"] if c["status"] == "passed")
        failed = len(result["cases"]) - passed
        console.print(f"Passed: {passed}  Failed: {failed}")

        if failed:
            ft = Table(title="Failure summary (first failing step per case)")
            ft.add_column("case_id", no_wrap=True)
            ft.add_column("title")
            ft.add_column("step")
            ft.add_column("message")
            for c in result.get("cases", []):
                if c.get("status") not in ("failed", "error"):
                    continue
                step_do = "-"
                msg = ""
                for s in c.get("steps", []) or []:
                    if s.get("status") in ("failed", "error"):
                        step_do = s.get("do") or "-"
                        err = s.get("error")
                        msg = _short_error(err, max_len=160)
                        break
                ft.add_row(str(c.get("id","")), str(c.get("title","")), str(step_do), msg)
            console.print(ft)


        if report:
            out = Path(report)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            console.print(f"Report: {out}")

        
        # Optional: pytest-based reports (does not rerun tests; converts JSON report -> pytest)
        if pytest_html or pytest_junitxml:
            try:
                # ensure we have a JSON report path; if not requested, write a default one
                if not report:
                    out = Path("out/report.json")
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                    console.print(f"Report: {out}")
                else:
                    out = Path(report)

                                # Typer should pass str, but be defensive if a list slips in
                if isinstance(pytest_html, builtins.list):
                    pytest_html = pytest_html[0] if pytest_html else None
                if isinstance(pytest_junitxml, builtins.list):
                    pytest_junitxml = pytest_junitxml[0] if pytest_junitxml else None
                pytest_html = _coerce_opt_str(pytest_html)
                pytest_junitxml = _coerce_opt_str(pytest_junitxml)
                html_path = Path(pytest_html) if pytest_html else None
                junit_path = Path(pytest_junitxml) if pytest_junitxml else None
                produced = generate_pytest_reports(
                    out,
                    html=html_path,
                    junitxml=junit_path,
                    title=str(doc.suite.name),
                    extra_args=list(pytest_arg or []),
                )
                if "html" in produced:
                    console.print(f"pytest-html: {produced['html']}")
                if "junitxml" in produced:
                    console.print(f"pytest-junitxml: {produced['junitxml']}")
            except Exception as e:
                # Forward compatible: keep legacy JSON report behavior even if pytest tooling is unavailable
                console.print(f"[yellow]WARN[/yellow] pytest reporting not generated: {e}")
        _exit(0 if failed == 0 else 1)

    except (ParseError, SpecVersionError, ValidationError) as e:
        _exit(2, f"ERROR: {e}")
    except ExecutionError as e:
        _exit(3, f"RUNTIME ERROR: {e}")






@app.command()
def analyze_log(
    path: Path = typer.Argument(..., help="Path to a log file (Appium/Selenium/etc.)"),
):
    """Analyze logs and print actionable fixes."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    findings = []

    # Appium: missing activity
    m = re.search(r"Activity class \{([^}]+)\} does not exist", txt)
    if m:
        findings.append(("appium.activity_not_found", m.group(1)))

    # Appium: missing ANDROID_HOME
    if "Neither ANDROID_HOME nor ANDROID_SDK_ROOT" in txt:
        findings.append(("android.sdk_env_missing", ""))

    # Connection refused to Appium server
    if "Max retries exceeded with url: /session" in txt or "NewConnectionError" in txt:
        findings.append(("appium.server_unreachable", ""))

    if not findings:
        console.print("[green]No known fatal patterns found.[/green]")
        _exit(0)

    for kind, detail in findings:
        if kind == "appium.activity_not_found":
            console.print("[red]Appium: Activity not found[/red]")
            console.print(f"  detail: {detail}")
            console.print("  Fix: set correct appActivity for your app. Run:")
            console.print("    adb shell cmd package resolve-activity --brief <appPackage>")
            console.print("  Then set appActivity to the returned activity (expand leading '.' to full package).")
        elif kind == "android.sdk_env_missing":
            console.print("[red]Android SDK env missing[/red]")
            console.print("  Fix: set ANDROID_SDK_ROOT (or ANDROID_HOME) to your SDK path.")
        elif kind == "appium.server_unreachable":
            console.print("[red]Appium server unreachable[/red]")
            console.print("  Fix: start appium and confirm /status:")
            console.print("    appium --address 127.0.0.1 --port 4723")
            console.print("    curl http://127.0.0.1:4723/status")
    _exit(1)


@app.command()
def versions(
    appium_server: Optional[str] = typer.Option(None, "--appium-server", help="Optionally query Appium server /status"),
):
    """Show tspec-runner and dependency versions."""
    from . import __version__ as _tspec_version
    import platform
    from importlib import metadata
    console.print(f"tspec-runner: {_tspec_version}")
    console.print(f"python: {platform.python_version()} ({platform.platform()})")

    def _v(pkg: str) -> str:
        try:
            return metadata.version(pkg)
        except Exception:
            return "not-installed"

    console.print(f"pytest: {_v('pytest')}")
    console.print(f"pytest-html: {_v('pytest-html')}")
    console.print(f"selenium: {_v('selenium')}")
    console.print(f"pywinauto: {_v('pywinauto')}")
    console.print(f"Appium-Python-Client: {_v('Appium-Python-Client')}")

    # Optional: Appium server status (stdlib urllib; no extra deps)
    if appium_server:
        try:
            import json as _json
            from urllib.request import urlopen, Request

            url = appium_server.rstrip('/') + '/status'
            req = Request(url, headers={'User-Agent': 'tspec-runner'})
            with urlopen(req, timeout=3) as resp:
                status = resp.status
                body = resp.read().decode('utf-8', errors='replace')
            console.print(f"appium-server: HTTP {status}")
            # Pretty-print JSON if possible
            try:
                console.print_json(_json.dumps(_json.loads(body), ensure_ascii=False))
            except Exception:
                console.print(body)
        except Exception as e:
            console.print(f"[yellow]WARN[/yellow] cannot query appium server: {e}")





@app.command()
def pytest_report(
    report: str = typer.Argument(..., help="Path to tspec JSON report"),
    html: Optional[str] = typer.Option(None, "--html", help="Write pytest-html report (requires extras: report)"),
    junitxml: Optional[str] = typer.Option(None, "--junitxml", help="Write junitxml (requires extras: report)"),
    pytest_arg: List[str] = typer.Option([], "--pytest-arg", help="Extra arg passed to pytest (repeatable)"),
):
    """Generate pytest-based reports from an existing tspec JSON report."""
    try:
        out = Path(report)
        h = _coerce_opt_str(html)
        j = _coerce_opt_str(junitxml)
        produced = generate_pytest_reports(
            out,
            html=Path(h) if h else None,
            junitxml=Path(j) if j else None,
            extra_args=list(pytest_arg or []),
        )
        if "html" in produced:
            console.print(f"pytest-html: {produced['html']}")
        if "junitxml" in produced:
            console.print(f"pytest-junitxml: {produced['junitxml']}")
        _exit(0)
    except Exception as e:
        _exit(3, f"ERROR: {e}")


@app.command()
def asset(
    name: str = typer.Argument("list", help="Asset name, or 'list'"),
    to: Path = typer.Option(Path("."), "--to", help="Destination path (when extracting)"),
):
    """List or extract bundled helper assets (e.g., update.ps1)."""
    try:
        if name == "list":
            for a in list_assets():
                console.print(a)
            _exit(0)
        out = to
        # if --to points to a directory, write there with original filename
        if out.exists() and out.is_dir():
            out = out / name
        p = extract_asset(name, out)
        console.print(f"extracted: {p}")
        _exit(0)
    except Exception as e:
        _exit(3, f"ERROR: {e}")


@app.command()
def mcp(
    transport: str = typer.Option("stdio", "--transport", help="MCP transport: stdio or streamable-http"),
    workdir: Path = typer.Option(Path("."), "--workdir", help="Base directory for safe file access"),
    host: str = typer.Option("127.0.0.1", "--host", help="HTTP host (streamable-http only)"),
    port: int = typer.Option(8765, "--port", help="HTTP port (streamable-http only)"),
    unity_mcp_url: Optional[str] = typer.Option(
        None,
        "--unity-mcp-url",
        help="Unity MCP /mcp URL (sets UNITY_MCP_MCP_URL + UNITY_MCP_MODE)",
    ),
    blender_mcp_url: Optional[str] = typer.Option(
        None,
        "--blender-mcp-url",
        help="Blender MCP base URL (sets BLENDER_MCP_BASE_URL)",
    ),
):
    """Start MCP server exposing tspec tools for AI clients."""
    try:
        mcp_start(
            transport=transport,
            workdir=str(workdir),
            host=host,
            port=port,
            unity_mcp_url=unity_mcp_url,
            blender_mcp_url=blender_mcp_url,
        )
    except Exception as e:
        _exit(3, f"MCP ERROR: {e}")
