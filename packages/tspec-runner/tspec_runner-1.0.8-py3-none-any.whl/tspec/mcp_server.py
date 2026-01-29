from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import ExecutionError, ValidationError


def _resolve_workdir(workdir: Optional[str]) -> Path:
    wd = workdir or os.environ.get("TSPEC_WORKDIR") or os.getcwd()
    return Path(wd).resolve()


def _safe_path(workdir: Path, p: str) -> Path:
    """Resolve a path under workdir. Reject escapes."""
    if not p:
        raise ValidationError("path is required")
    rp = (workdir / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
    try:
        rp.relative_to(workdir)
    except Exception as e:
        raise ValidationError(f"path must be under workdir: {workdir} (got {rp})") from e
    return rp


def start(
    *,
    transport: str = "stdio",
    workdir: Optional[str] = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    """Start tspec MCP server.

    - stdio: recommended for local clients (Claude Desktop etc.)
    - streamable-http: for inspector / remote
    """
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ExecutionError("MCP support requires: pip install -e '.[mcp]'") from e

    from .manual_loader import discover_manuals, find_manual_by_id, load_manual
    from .doctor_android import check_android_env
    from .doctor_selenium import check_selenium_env
    from .doctor_ios import check_ios_env
    from .report_view import load_report as load_report_view, format_error_message
    from .programmatic import run_spec_file
    from .validate import load_and_validate

    wd = _resolve_workdir(workdir)

    mcp = FastMCP(
        name="tspec-runner",
        instructions=(
            "Tools to validate/run TSpec specs and inspect reports/manuals. Also includes optional Neko (m1k1o/neko) tools when NEKO_BASE_URL is set. "

            "For safety, all file paths are resolved under workdir."

        ),
    )

    # ---------- Tools ----------
    @mcp.tool()
    def tspec_validate(path: str) -> Dict[str, Any]:
        """Validate a spec and return resolved version + case count."""
        p = _safe_path(wd, path)
        doc, spec = load_and_validate(p)
        return {
            "path": str(p),
            "declared": getattr(spec, "declared", None),
            "resolved": str(spec.resolved),
            "case_count": len(doc.cases),
        }

    @mcp.tool()
    def tspec_run(
        path: str,
        backend: str = "selenium",
        report: str = "out/report.json",
        case_id: Optional[str] = None,  # reserved for future
    ) -> Dict[str, Any]:
        """Run a spec; writes report JSON and returns summary."""
        p = _safe_path(wd, path)
        r = _safe_path(wd, report)
        result = run_spec_file(p, backend=backend, report=r)
        passed = sum(1 for c in result.get("cases", []) if c.get("status") == "passed")
        failed = len(result.get("cases", [])) - passed
        return {"path": str(p), "backend": backend, "report": str(r), "passed": passed, "failed": failed}

    @mcp.tool()
    def tspec_report(
        report: str,
        only_errors: bool = False,
        case_id: Optional[str] = None,
        full_trace: bool = False,
        max_rows: int = 50,
    ) -> Dict[str, Any]:
        """Summarize a JSON report; returns rows (optionally only errors)."""
        rp = _safe_path(wd, report)
        rv = load_report_view(rp)

        rows = []
        for c in rv.cases:
            if case_id and c.id != case_id:
                continue
            for s in c.steps:
                status = s.status
                if only_errors and status == "passed":
                    continue
                msg = format_error_message(s.error, full_trace=full_trace) if s.error else ""
                rows.append(
                    {
                        "case_id": c.id,
                        "title": c.title,
                        "step": s.do if s.name is None else f"{s.do} ({s.name})",
                        "status": status,
                        "message": msg,
                    }
                )

        summary = {
            "cases_total": len(rv.cases),
            "steps_total": sum(len(c.steps) for c in rv.cases),
            "rows_returned": min(len(rows), max_rows),
            "truncated": len(rows) > max_rows,
        }
        return {"report": str(rp), "summary": summary, "rows": rows[:max_rows]}

    @mcp.tool()
    def tspec_manual_list(base: str = "docs") -> Dict[str, Any]:
        b = _safe_path(wd, base)
        items = discover_manuals(b)
        return {
            "base": str(b),
            "manuals": [
                {"id": mf.manual.id, "title": mf.manual.title, "tags": mf.manual.tags, "path": str(p)}
                for p, mf in items
            ],
        }

    @mcp.tool()
    def tspec_manual_show(target: str, base: str = "docs", full: bool = False) -> Dict[str, Any]:
        tp = Path(target)
        if tp.exists():
            p = _safe_path(wd, target)
            mf = load_manual(p)
        else:
            b = _safe_path(wd, base)
            p, mf = find_manual_by_id(b, target)
        man = mf.manual
        out: Dict[str, Any] = {
            "id": man.id,
            "title": man.title,
            "tags": man.tags,
            "summary": man.summary,
            "prerequisites": man.prerequisites,
            "steps": [{"title": s.title, "body": s.body} for s in man.steps],
        }
        if full:
            out["troubleshooting"] = [{"title": s.title, "body": s.body} for s in man.troubleshooting]
            out["references"] = man.references
        return out

    @mcp.tool()
    def tspec_doctor(android: bool = False, selenium: bool = False, ios: bool = False) -> Dict[str, Any]:
        out: Dict[str, Any] = {"workdir": str(wd), "checks": {}}
        if android:
            out["checks"]["android"] = [c.__dict__ for c in check_android_env()]
        if selenium:
            out["checks"]["selenium"] = [c.__dict__ for c in check_selenium_env()]
        if ios:
            out["checks"]["ios"] = [c.__dict__ for c in check_ios_env()]
        return out



    # ---------- Neko Tools (m1k1o/neko) ----------
    # Enabled when NEKO_BASE_URL is set.
    from .neko_client import NekoAuth, NekoClient, _parse_allowlist_hosts

    def _tool(name: str):
        """Register a tool name; fallback if FastMCP doesn't support `name=`."""
        try:
            return mcp.tool(name=name)  # type: ignore[arg-type]
        except TypeError:
            return mcp.tool()

    _neko_state: Dict[str, Any] = {}

    def _get_neko() -> NekoClient:
        if "client" in _neko_state:
            return _neko_state["client"]

        base_url = os.environ.get("NEKO_BASE_URL", "").strip()
        if not base_url:
            raise ValidationError("NEKO_BASE_URL is required to use neko tools")

        allow = _parse_allowlist_hosts(os.environ.get("NEKO_ALLOWLIST_HOSTS"))
        auth_mode = (os.environ.get("NEKO_AUTH_MODE") or "cookie").strip()
        auth = NekoAuth(
            mode=auth_mode,
            bearer_token=os.environ.get("NEKO_BEARER_TOKEN"),
            token_query=os.environ.get("NEKO_TOKEN_QUERY"),
            username=os.environ.get("NEKO_USERNAME"),
            password=os.environ.get("NEKO_PASSWORD"),
        )
        timeout_ms = int(os.environ.get("NEKO_TIMEOUT_MS") or "10000")
        verify_tls = (os.environ.get("NEKO_VERIFY_TLS") or "true").lower() not in {"0", "false", "no"}

        client = NekoClient(base_url=base_url, auth=auth, timeout_ms=timeout_ms, allowlist_hosts=allow, verify_tls=verify_tls)
        _neko_state["client"] = client
        return client

    @_tool("neko.config")
    def neko_config() -> Dict[str, Any]:
        """Show current Neko connection config (secrets redacted)."""
        base_url = os.environ.get("NEKO_BASE_URL", "").strip()
        return {
            "base_url": base_url,
            "auth_mode": (os.environ.get("NEKO_AUTH_MODE") or "cookie").strip(),
            "allowlist_hosts": _parse_allowlist_hosts(os.environ.get("NEKO_ALLOWLIST_HOSTS")),
            "timeout_ms": int(os.environ.get("NEKO_TIMEOUT_MS") or "10000"),
            "verify_tls": (os.environ.get("NEKO_VERIFY_TLS") or "true").lower() not in {"0", "false", "no"},
        }

    @_tool("neko.health")
    def neko_health() -> Dict[str, Any]:
        """GET /health (no auth)."""
        c = _get_neko()
        r = c.request("GET", "/health", auth_required=False)
        return {"ok": True, "status_code": r.status_code, "body": r.text}

    @_tool("neko.metrics")
    def neko_metrics() -> Dict[str, Any]:
        """GET /metrics (no auth)."""
        c = _get_neko()
        r = c.request("GET", "/metrics", auth_required=False)
        return {"ok": True, "status_code": r.status_code, "prometheus": r.text}

    @_tool("neko.stats")
    def neko_stats() -> Dict[str, Any]:
        """GET /api/stats."""
        return _get_neko().get_json("/api/stats")

    @_tool("neko.login")
    def neko_login(username: Optional[str] = None, password: Optional[str] = None, redact_token: bool = True) -> Dict[str, Any]:
        """POST /api/login (cookie or token)."""
        res = _get_neko().login(username=username, password=password)
        if redact_token and isinstance(res, dict) and "token" in res:
            res = dict(res)
            res["token"] = "***"
        return res

    @_tool("neko.whoami")
    def neko_whoami() -> Dict[str, Any]:
        """GET /api/whoami."""
        return _get_neko().get_json("/api/whoami")

    @_tool("neko.sessions.list")
    def neko_sessions_list() -> Dict[str, Any]:
        """GET /api/sessions."""
        return {"sessions": _get_neko().get_json("/api/sessions")}

    @_tool("neko.sessions.disconnect")
    def neko_sessions_disconnect(session_id: str) -> Dict[str, Any]:
        """POST /api/sessions/{sessionId}/disconnect."""
        if not session_id:
            raise ValidationError("session_id is required")
        return _get_neko().post_json(f"/api/sessions/{session_id}/disconnect", json={})

    @_tool("neko.sessions.remove")
    def neko_sessions_remove(session_id: str) -> Dict[str, Any]:
        """DELETE /api/sessions/{sessionId}."""
        if not session_id:
            raise ValidationError("session_id is required")
        return _get_neko().delete_json(f"/api/sessions/{session_id}")

    @_tool("neko.room.settings.get")
    def neko_room_settings_get() -> Dict[str, Any]:
        """GET /api/room/settings."""
        return _get_neko().get_json("/api/room/settings")

    @_tool("neko.room.settings.set")
    def neko_room_settings_set(settings: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/room/settings."""
        if not isinstance(settings, dict):
            raise ValidationError("settings must be an object")
        return _get_neko().post_json("/api/room/settings", json=settings)

    @_tool("neko.room.control.get")
    def neko_room_control_get() -> Dict[str, Any]:
        """GET /api/room/control."""
        return _get_neko().get_json("/api/room/control")

    @_tool("neko.room.control.take")
    def neko_room_control_take() -> Dict[str, Any]:
        """POST /api/room/control/take."""
        return _get_neko().post_json("/api/room/control/take", json={})

    @_tool("neko.room.control.release")
    def neko_room_control_release() -> Dict[str, Any]:
        """POST /api/room/control/release."""
        return _get_neko().post_json("/api/room/control/release", json={})

    @_tool("neko.room.control.request")
    def neko_room_control_request() -> Dict[str, Any]:
        """POST /api/room/control/request."""
        return _get_neko().post_json("/api/room/control/request", json={})

    @_tool("neko.room.control.reset")
    def neko_room_control_reset() -> Dict[str, Any]:
        """POST /api/room/control/reset."""
        return _get_neko().post_json("/api/room/control/reset", json={})

    @_tool("neko.room.control.give")
    def neko_room_control_give(session_id: str) -> Dict[str, Any]:
        """POST /api/room/control/give/{sessionId}."""
        if not session_id:
            raise ValidationError("session_id is required")
        return _get_neko().post_json(f"/api/room/control/give/{session_id}", json={})

    @_tool("neko.screen.get")
    def neko_screen_get() -> Dict[str, Any]:
        """GET /api/room/screen."""
        return _get_neko().get_json("/api/room/screen")

    @_tool("neko.screen.configurations")
    def neko_screen_configurations() -> Dict[str, Any]:
        """GET /api/room/screen/configurations."""
        return {"configurations": _get_neko().get_json("/api/room/screen/configurations")}

    @_tool("neko.screen.set")
    def neko_screen_set(width: int, height: int, rate: int = 30) -> Dict[str, Any]:
        """POST /api/room/screen."""
        return _get_neko().post_json("/api/room/screen", json={"width": int(width), "height": int(height), "rate": int(rate)})

    @_tool("neko.screen.screenshot")
    def neko_screen_screenshot(quality: int = 80) -> Dict[str, Any]:
        """GET /api/room/screen/shot.jpg -> base64."""
        return _get_neko().screenshot_jpg(quality=quality, cast=False)

    @_tool("neko.screen.screencast")
    def neko_screen_screencast(quality: int = 80) -> Dict[str, Any]:
        """GET /api/room/screen/cast.jpg -> base64."""
        return _get_neko().screenshot_jpg(quality=quality, cast=True)

    @_tool("neko.clipboard.get")
    def neko_clipboard_get() -> Dict[str, Any]:
        """GET /api/room/clipboard."""
        return _get_neko().get_json("/api/room/clipboard")

    @_tool("neko.clipboard.set")
    def neko_clipboard_set(text: Optional[str] = None, html: Optional[str] = None) -> Dict[str, Any]:
        """POST /api/room/clipboard."""
        payload: Dict[str, Any] = {}
        if text is not None:
            payload["text"] = text
        if html is not None:
            payload["html"] = html
        if not payload:
            raise ValidationError("text or html is required")
        return _get_neko().post_json("/api/room/clipboard", json=payload)

    @_tool("neko.clipboard.image")
    def neko_clipboard_image() -> Dict[str, Any]:
        """GET /api/room/clipboard/image.png -> base64."""
        return _get_neko().clipboard_image_png()

    @_tool("neko.upload.drop")
    def neko_upload_drop(x: int, y: int, files: list) -> Dict[str, Any]:
        """POST /api/room/upload/drop (multipart). files=[{name, bytes_base64, content_type?}]"""
        return _get_neko().upload_multipart(
            "/api/room/upload/drop",
            fields={"x": int(x), "y": int(y)},
            files_b64=files,
        )

    @_tool("neko.upload.dialog")
    def neko_upload_dialog(files: list) -> Dict[str, Any]:
        """POST /api/room/upload/dialog (multipart)."""
        return _get_neko().upload_multipart(
            "/api/room/upload/dialog",
            fields={},
            files_b64=files,
        )

    @_tool("neko.upload.dialog.close")
    def neko_upload_dialog_close() -> Dict[str, Any]:
        """DELETE /api/room/upload/dialog."""
        return _get_neko().delete_json("/api/room/upload/dialog")

    @_tool("neko.members.list")
    def neko_members_list(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """GET /api/members?limit=&offset="""
        return {"members": _get_neko().get_json("/api/members", params={"limit": int(limit), "offset": int(offset)})}

    @_tool("neko.members.create")
    def neko_members_create(member: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/members"""
        if not isinstance(member, dict):
            raise ValidationError("member must be an object")
        return _get_neko().post_json("/api/members", json=member)

    @_tool("neko.members.get")
    def neko_members_get(member_id: str) -> Dict[str, Any]:
        """GET /api/members/{memberId}"""
        if not member_id:
            raise ValidationError("member_id is required")
        return _get_neko().get_json(f"/api/members/{member_id}")

    @_tool("neko.members.set")
    def neko_members_set(member_id: str, member: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/members/{memberId}"""
        if not member_id:
            raise ValidationError("member_id is required")
        if not isinstance(member, dict):
            raise ValidationError("member must be an object")
        return _get_neko().post_json(f"/api/members/{member_id}", json=member)

    @_tool("neko.members.delete")
    def neko_members_delete(member_id: str) -> Dict[str, Any]:
        """DELETE /api/members/{memberId}"""
        if not member_id:
            raise ValidationError("member_id is required")
        return _get_neko().delete_json(f"/api/members/{member_id}")

    @_tool("neko.members.password.set")
    def neko_members_password_set(member_id: str, password: str) -> Dict[str, Any]:
        """POST /api/members/{memberId}/password"""
        if not member_id:
            raise ValidationError("member_id is required")
        if password is None or password == "":
            raise ValidationError("password is required")
        return _get_neko().post_json(f"/api/members/{member_id}/password", json={"password": password})

    @_tool("neko.members.bulk.update")
    def neko_members_bulk_update(body: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/members_bulk/update"""
        if not isinstance(body, dict):
            raise ValidationError("body must be an object")
        return _get_neko().post_json("/api/members_bulk/update", json=body)

    @_tool("neko.members.bulk.delete")
    def neko_members_bulk_delete(body: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/members_bulk/delete"""
        if not isinstance(body, dict):
            raise ValidationError("body must be an object")
        return _get_neko().post_json("/api/members_bulk/delete", json=body)


    # ---------- Blender MCP Tools ----------
    # Enabled when BLENDER_MCP_BASE_URL is set.
    _blender_state: Dict[str, Any] = {}

    def _get_blender():
        if "client" in _blender_state:
            return _blender_state["client"]

        base_url = os.environ.get("BLENDER_MCP_BASE_URL", "").strip()
        if not base_url:
            raise ValidationError("BLENDER_MCP_BASE_URL is required to use blender tools")

        try:
            from .blender_client import BlenderAuth, BlenderClient, _parse_allowlist_hosts
        except Exception as e:  # pragma: no cover
            raise ExecutionError("Blender MCP support requires: pip install -e '.[blender]'") from e

        allow = _parse_allowlist_hosts(os.environ.get("BLENDER_MCP_ALLOWLIST_HOSTS"))
        auth_mode = (os.environ.get("BLENDER_MCP_AUTH_MODE") or "none").strip()
        auth = BlenderAuth(
            mode=auth_mode,
            bearer_token=os.environ.get("BLENDER_MCP_BEARER_TOKEN"),
            token_query=os.environ.get("BLENDER_MCP_TOKEN_QUERY"),
        )
        timeout_ms = int(os.environ.get("BLENDER_MCP_TIMEOUT_MS") or "10000")
        verify_tls = (os.environ.get("BLENDER_MCP_VERIFY_TLS") or "true").lower() not in {"0", "false", "no"}

        client = BlenderClient(
            base_url=base_url,
            auth=auth,
            timeout_ms=timeout_ms,
            allowlist_hosts=allow,
            verify_tls=verify_tls,
        )
        _blender_state["client"] = client
        return client

    @_tool("blender.config")
    def blender_config() -> Dict[str, Any]:
        """Show current Blender MCP config (secrets redacted)."""
        base_url = os.environ.get("BLENDER_MCP_BASE_URL", "").strip()
        return {
            "base_url": base_url,
            "auth_mode": (os.environ.get("BLENDER_MCP_AUTH_MODE") or "none").strip(),
            "allowlist_hosts": os.environ.get("BLENDER_MCP_ALLOWLIST_HOSTS", ""),
            "timeout_ms": int(os.environ.get("BLENDER_MCP_TIMEOUT_MS") or "10000"),
            "verify_tls": (os.environ.get("BLENDER_MCP_VERIFY_TLS") or "true").lower() not in {"0", "false", "no"},
        }

    @_tool("blender.health")
    def blender_health() -> Dict[str, Any]:
        """GET /health (no auth)."""
        c = _get_blender()
        r = c.request("GET", "/health", auth_required=False)
        return {"ok": True, "status_code": r.status_code, "body": r.text}

    @_tool("blender.rpc")
    def blender_rpc(method: str, params: Optional[Dict[str, Any]] = None, path: str = "/rpc") -> Dict[str, Any]:
        """POST /rpc {method, params}."""
        return _get_blender().rpc(method, params=params, path=path)


    # ---------- Unity MCP Tools ----------
    # Enabled when UNITY_MCP_BASE_URL is set.
    _unity_state: Dict[str, Any] = {}
    _unity_mcp_state: Dict[str, Any] = {}

    def _unity_mode() -> str:
        raw = (os.environ.get("UNITY_MCP_MODE") or "").strip().lower()
        if raw:
            return raw
        if os.environ.get("UNITY_MCP_MCP_URL"):
            return "mcp-http"
        return "rest"

    def _unity_mcp_url() -> str:
        mcp_url = os.environ.get("UNITY_MCP_MCP_URL", "").strip()
        if mcp_url:
            return mcp_url
        base_url = os.environ.get("UNITY_MCP_BASE_URL", "").strip()
        if not base_url:
            return ""
        return f"{base_url.rstrip('/')}/mcp"

    def _get_unity():
        if "client" in _unity_state:
            return _unity_state["client"]

        base_url = os.environ.get("UNITY_MCP_BASE_URL", "").strip()
        if not base_url:
            raise ValidationError("UNITY_MCP_BASE_URL is required to use unity tools")

        try:
            from .unity_client import UnityAuth, UnityClient, _parse_allowlist_hosts
        except Exception as e:  # pragma: no cover
            raise ExecutionError("Unity MCP support requires: pip install -e '.[unity]'") from e

        allow = _parse_allowlist_hosts(os.environ.get("UNITY_MCP_ALLOWLIST_HOSTS"))
        auth_mode = (os.environ.get("UNITY_MCP_AUTH_MODE") or "none").strip()
        auth = UnityAuth(
            mode=auth_mode,
            bearer_token=os.environ.get("UNITY_MCP_BEARER_TOKEN"),
            token_query=os.environ.get("UNITY_MCP_TOKEN_QUERY"),
        )
        timeout_ms = int(os.environ.get("UNITY_MCP_TIMEOUT_MS") or "10000")
        verify_tls = (os.environ.get("UNITY_MCP_VERIFY_TLS") or "true").lower() not in {"0", "false", "no"}

        client = UnityClient(
            base_url=base_url,
            auth=auth,
            timeout_ms=timeout_ms,
            allowlist_hosts=allow,
            verify_tls=verify_tls,
        )
        _unity_state["client"] = client
        return client

    def _get_unity_mcp_http():
        if "client" in _unity_mcp_state:
            return _unity_mcp_state["client"]

        mcp_url = _unity_mcp_url()
        if not mcp_url:
            raise ValidationError("UNITY_MCP_MCP_URL or UNITY_MCP_BASE_URL is required to use unity.tool")

        try:
            from .unity_client import UnityAuth, UnityMcpHttpClient, _parse_allowlist_hosts
        except Exception as e:  # pragma: no cover
            raise ExecutionError("Unity MCP HTTP support requires: pip install -e '.[unity,mcp]'") from e

        allow = _parse_allowlist_hosts(os.environ.get("UNITY_MCP_ALLOWLIST_HOSTS"))
        auth_mode = (os.environ.get("UNITY_MCP_AUTH_MODE") or "none").strip()
        auth = UnityAuth(
            mode=auth_mode,
            bearer_token=os.environ.get("UNITY_MCP_BEARER_TOKEN"),
            token_query=os.environ.get("UNITY_MCP_TOKEN_QUERY"),
        )
        timeout_ms = int(os.environ.get("UNITY_MCP_TIMEOUT_MS") or "10000")
        verify_tls = (os.environ.get("UNITY_MCP_VERIFY_TLS") or "true").lower() not in {"0", "false", "no"}

        client = UnityMcpHttpClient(
            mcp_url=mcp_url,
            auth=auth,
            timeout_ms=timeout_ms,
            allowlist_hosts=allow,
            verify_tls=verify_tls,
        )
        _unity_mcp_state["client"] = client
        return client

    @_tool("unity.config")
    def unity_config() -> Dict[str, Any]:
        """Show current Unity MCP config (secrets redacted)."""
        base_url = os.environ.get("UNITY_MCP_BASE_URL", "").strip()
        return {
            "base_url": base_url,
            "mcp_url": _unity_mcp_url(),
            "mode": _unity_mode(),
            "auth_mode": (os.environ.get("UNITY_MCP_AUTH_MODE") or "none").strip(),
            "allowlist_hosts": os.environ.get("UNITY_MCP_ALLOWLIST_HOSTS", ""),
            "timeout_ms": int(os.environ.get("UNITY_MCP_TIMEOUT_MS") or "10000"),
            "verify_tls": (os.environ.get("UNITY_MCP_VERIFY_TLS") or "true").lower() not in {"0", "false", "no"},
        }

    @_tool("unity.health")
    def unity_health() -> Dict[str, Any]:
        """GET /health (no auth)."""
        c = _get_unity()
        r = c.request("GET", "/health", auth_required=False)
        return {"ok": True, "status_code": r.status_code, "body": r.text}

    @_tool("unity.rpc")
    def unity_rpc(method: str, params: Optional[Dict[str, Any]] = None, path: str = "/rpc") -> Dict[str, Any]:
        """POST /rpc {method, params}."""
        return _get_unity().rpc(method, params=params, path=path)

    @_tool("unity.tool")
    def unity_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a Unity MCP tool via streamable HTTP."""
        mode = _unity_mode()
        if mode not in {"mcp-http", "mcp_http", "mcp"}:
            raise ValidationError("unity.tool requires UNITY_MCP_MODE=mcp-http")
        return _get_unity_mcp_http().call_tool(name, arguments or {})


    # ---------- Resources (read-only) ----------
    @mcp.resource("file://workdir")
    def workdir_info() -> str:
        return str(wd)

    # Run
    if transport not in {"stdio", "streamable-http"}:
        raise ExecutionError("transport must be 'stdio' or 'streamable-http'")

    if transport == "streamable-http":
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
