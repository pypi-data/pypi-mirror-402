from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

import httpx

from .errors import ExecutionError, ValidationError


def _parse_allowlist_hosts(raw: Optional[str]) -> Tuple[str, ...]:
    if not raw:
        return tuple()
    parts = [p.strip() for p in raw.split(",")]
    return tuple(p for p in parts if p)


def _hostport(u: httpx.URL) -> str:
    host = u.host or ""
    if u.port:
        return f"{host}:{u.port}"
    return host


@dataclass
class UnityAuth:
    mode: str = "none"  # none | bearer | token
    bearer_token: Optional[str] = None
    token_query: Optional[str] = None


class UnityClient:
    """Thin REST client for Unity MCP endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        auth: Optional[UnityAuth] = None,
        timeout_ms: int = 10_000,
        allowlist_hosts: Optional[Iterable[str]] = None,
        verify_tls: bool = True,
    ) -> None:
        if not base_url:
            raise ValidationError("UNITY_MCP_BASE_URL is required")
        self.base_url = base_url.rstrip("/")
        self.auth = auth or UnityAuth()

        self._timeout = httpx.Timeout(timeout_ms / 1000.0)
        self._client = httpx.Client(base_url=self.base_url, timeout=self._timeout, verify=verify_tls)

        allow = tuple(allowlist_hosts or ())
        if allow:
            u = httpx.URL(self.base_url)
            hp = _hostport(u)
            if (u.host not in allow) and (hp not in allow):
                raise ValidationError(
                    f"UNITY_MCP_BASE_URL host not allowed: {u.host} (hostport={hp}). "
                    f"Allowed: {', '.join(allow)}"
                )

    def _apply_auth(self, headers: Dict[str, str], params: Dict[str, Any]) -> None:
        mode = (self.auth.mode or "none").lower().strip()
        if mode in {"none", ""}:
            return
        if mode == "bearer":
            if not self.auth.bearer_token:
                raise ValidationError("UNITY_MCP_BEARER_TOKEN is required for bearer auth")
            headers["Authorization"] = f"Bearer {self.auth.bearer_token}"
        elif mode == "token":
            if not self.auth.token_query:
                raise ValidationError("UNITY_MCP_TOKEN_QUERY is required for token auth")
            params.setdefault("token", self.auth.token_query)
        else:
            raise ValidationError("UNITY_MCP_AUTH_MODE must be one of: none, bearer, token")

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_required: bool = True,
    ) -> httpx.Response:
        params = dict(params or {})
        headers = dict(headers or {})

        if auth_required:
            self._apply_auth(headers, params)

        try:
            resp = self._client.request(
                method.upper(),
                path,
                params=params,
                json=json,
                headers=headers,
            )
        except httpx.HTTPError as e:
            raise ExecutionError(f"Unity MCP request failed: {method} {path}: {e}") from e

        if resp.status_code >= 400:
            body = resp.text
            if len(body) > 800:
                body = body[:800] + "...(truncated)"
            raise ExecutionError(f"Unity MCP error {resp.status_code} on {method} {path}: {body}")
        return resp

    def get_json(self, path: str, *, params: Optional[Dict[str, Any]] = None, auth_required: bool = True) -> Dict[str, Any]:
        return self.request("GET", path, params=params, auth_required=auth_required).json()

    def post_json(
        self, path: str, *, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, auth_required: bool = True
    ) -> Dict[str, Any]:
        resp = self.request("POST", path, params=params, json=json, auth_required=auth_required)
        if not resp.content:
            return {"ok": True}
        try:
            return resp.json()
        except Exception:
            return {"ok": True, "raw": resp.text}

    def rpc(self, method: str, params: Optional[Dict[str, Any]] = None, path: str = "/rpc") -> Dict[str, Any]:
        if not method:
            raise ValidationError("method is required")
        payload = {"method": method, "params": params or {}}
        return self.post_json(path, json=payload)

    def close(self) -> None:
        self._client.close()


def _apply_token_query(url: str, token: str) -> str:
    u = httpx.URL(url)
    params = dict(u.params)
    params.setdefault("token", token)
    return str(u.copy_with(params=params))


class UnityMcpHttpClient:
    """Streamable HTTP MCP client for Unity MCP server."""

    def __init__(
        self,
        *,
        mcp_url: str,
        auth: Optional[UnityAuth] = None,
        timeout_ms: int = 10_000,
        allowlist_hosts: Optional[Iterable[str]] = None,
        verify_tls: bool = True,
    ) -> None:
        if not mcp_url:
            raise ValidationError("UNITY_MCP_MCP_URL is required")
        self.mcp_url = mcp_url
        self.auth = auth or UnityAuth()
        self.timeout_ms = timeout_ms
        self.verify_tls = verify_tls

        allow = tuple(allowlist_hosts or ())
        if allow:
            u = httpx.URL(self.mcp_url)
            hp = _hostport(u)
            if (u.host not in allow) and (hp not in allow):
                raise ValidationError(
                    f"UNITY_MCP_MCP_URL host not allowed: {u.host} (hostport={hp}). "
                    f"Allowed: {', '.join(allow)}"
                )

    def _apply_auth(self, headers: Dict[str, str]) -> str:
        mode = (self.auth.mode or "none").lower().strip()
        if mode in {"none", ""}:
            return self.mcp_url
        if mode == "bearer":
            if not self.auth.bearer_token:
                raise ValidationError("UNITY_MCP_BEARER_TOKEN is required for bearer auth")
            headers["Authorization"] = f"Bearer {self.auth.bearer_token}"
            return self.mcp_url
        if mode == "token":
            if not self.auth.token_query:
                raise ValidationError("UNITY_MCP_TOKEN_QUERY is required for token auth")
            return _apply_token_query(self.mcp_url, self.auth.token_query)
        raise ValidationError("UNITY_MCP_AUTH_MODE must be one of: none, bearer, token")

    async def _call_tool_async(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from mcp.client import streamable_http
            from mcp.client.session import ClientSession
        except Exception as e:  # pragma: no cover
            raise ExecutionError("Unity MCP HTTP client requires: pip install -e '.[mcp]'") from e

        headers: Dict[str, str] = {}
        url = self._apply_auth(headers)
        timeout_seconds = self.timeout_ms / 1000.0

        def _client_factory(headers: Dict[str, str] | None = None, timeout: httpx.Timeout | None = None, auth=None):
            return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, verify=self.verify_tls)

        async with streamable_http.streamablehttp_client(
            url,
            headers=headers,
            timeout=timeout_seconds,
            httpx_client_factory=_client_factory,
        ) as (read_stream, write_stream, _get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                return result.model_dump()

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not name:
            raise ValidationError("tool name is required")
        try:
            import anyio
        except Exception as e:  # pragma: no cover
            raise ExecutionError("Unity MCP HTTP client requires: pip install -e '.[mcp]'") from e
        return anyio.run(self._call_tool_async, name, arguments or {})
