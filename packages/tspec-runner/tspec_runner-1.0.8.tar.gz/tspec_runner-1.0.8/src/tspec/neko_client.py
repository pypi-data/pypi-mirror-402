from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib.parse import urlparse

import httpx

from .errors import ExecutionError, ValidationError


def _parse_allowlist_hosts(raw: Optional[str]) -> Tuple[str, ...]:
    """
    Comma-separated allowlist like:
      "neko.local,neko.local:8080,10.0.0.5:8080"
    """
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
class NekoAuth:
    mode: str = "cookie"  # cookie | bearer | token
    bearer_token: Optional[str] = None
    token_query: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class NekoClient:
    """
    Thin REST client for m1k1o/neko API.

    Notes:
    - This client purposefully does NOT expose arbitrary URL control to avoid SSRF.
    - Enforce allowlist via NEKO_ALLOWLIST_HOSTS.
    """

    def __init__(
        self,
        *,
        base_url: str,
        auth: Optional[NekoAuth] = None,
        timeout_ms: int = 10_000,
        allowlist_hosts: Optional[Iterable[str]] = None,
        verify_tls: bool = True,
    ) -> None:
        if not base_url:
            raise ValidationError("NEKO_BASE_URL is required")
        self.base_url = base_url.rstrip("/")
        self.auth = auth or NekoAuth()

        self._timeout = httpx.Timeout(timeout_ms / 1000.0)
        self._client = httpx.Client(base_url=self.base_url, timeout=self._timeout, verify=verify_tls)

        # SSRF guard
        allow = tuple(allowlist_hosts or ())
        if allow:
            u = httpx.URL(self.base_url)
            hp = _hostport(u)
            if (u.host not in allow) and (hp not in allow):
                raise ValidationError(
                    f"NEKO_BASE_URL host not allowed: {u.host} (hostport={hp}). "
                    f"Allowed: {', '.join(allow)}"
                )

    # ---------- auth helpers ----------
    def _apply_auth(self, headers: Dict[str, str], params: Dict[str, Any]) -> None:
        mode = (self.auth.mode or "cookie").lower().strip()
        if mode == "bearer":
            if not self.auth.bearer_token:
                raise ValidationError("NEKO_BEARER_TOKEN is required for bearer auth")
            headers["Authorization"] = f"Bearer {self.auth.bearer_token}"
        elif mode == "token":
            if not self.auth.token_query:
                raise ValidationError("NEKO_TOKEN_QUERY is required for token auth")
            params.setdefault("token", self.auth.token_query)
        elif mode == "cookie":
            # cookie is handled by httpx Client cookie jar
            pass
        else:
            raise ValidationError("NEKO_AUTH_MODE must be one of: cookie, bearer, token")

    def login(self, *, username: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        POST /api/login (cookie session or token response depending on Neko config).
        """
        u = username or self.auth.username or os.environ.get("NEKO_USERNAME")
        p = password or self.auth.password or os.environ.get("NEKO_PASSWORD")
        if not u or not p:
            raise ValidationError("username/password are required (or set NEKO_USERNAME/NEKO_PASSWORD)")
        return self.post_json("/api/login", json={"username": u, "password": p}, auth_required=False)

    # ---------- generic requests ----------
    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
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
                files=files,
                data=data,
                headers=headers,
            )
        except httpx.HTTPError as e:
            raise ExecutionError(f"Neko request failed: {method} {path}: {e}") from e

        if resp.status_code >= 400:
            # keep body short; neko sometimes returns text/html
            body = resp.text
            if len(body) > 800:
                body = body[:800] + "...(truncated)"
            raise ExecutionError(f"Neko API error {resp.status_code} on {method} {path}: {body}")
        return resp

    def get_json(self, path: str, *, params: Optional[Dict[str, Any]] = None, auth_required: bool = True) -> Dict[str, Any]:
        return self.request("GET", path, params=params, auth_required=auth_required).json()

    def post_json(
        self, path: str, *, json: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, auth_required: bool = True
    ) -> Dict[str, Any]:
        """
        POST that returns JSON if present, otherwise {"ok": True}.
        Neko uses 204 No Content for many endpoints.
        """
        resp = self.request("POST", path, params=params, json=json, auth_required=auth_required)
        if not resp.content:
            return {"ok": True}
        try:
            return resp.json()
        except Exception:
            return {"ok": True, "raw": resp.text}

    def delete_json(self, path: str, *, params: Optional[Dict[str, Any]] = None, auth_required: bool = True) -> Dict[str, Any]:
        # some endpoints return empty; normalize
        resp = self.request("DELETE", path, params=params, auth_required=auth_required)
        if not resp.content:
            return {"ok": True}
        try:
            return resp.json()
        except Exception:
            return {"ok": True, "raw": resp.text}


    def get_bytes(self, path: str, *, params: Optional[Dict[str, Any]] = None, auth_required: bool = True) -> bytes:
        return self.request("GET", path, params=params, auth_required=auth_required).content

    # ---------- convenience ----------
    def screenshot_jpg(self, *, quality: int = 80, cast: bool = False) -> Dict[str, Any]:
        q = max(0, min(100, int(quality)))
        endpoint = "/api/room/screen/cast.jpg" if cast else "/api/room/screen/shot.jpg"
        b = self.get_bytes(endpoint, params={"quality": q})
        return {
            "mime": "image/jpeg",
            "quality": q,
            "bytes": len(b),
            "data_base64": base64.b64encode(b).decode("ascii"),
        }

    def clipboard_image_png(self) -> Dict[str, Any]:
        b = self.get_bytes("/api/room/clipboard/image.png")
        return {
            "mime": "image/png",
            "bytes": len(b),
            "data_base64": base64.b64encode(b).decode("ascii"),
        }

    def upload_multipart(
        self,
        path: str,
        *,
        fields: Optional[Dict[str, Any]] = None,
        files_b64: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Helper for endpoints that accept multipart/form-data.

        files_b64: [{name: str, bytes_base64: str, content_type?: str}]
        """
        fields = dict(fields or {})
        files: Dict[str, Any] = {}
        if files_b64:
            # Neko expects "files" field (array). httpx supports repeated fields by list of tuples;
            # easiest is build a list of ("files", (...)) and pass via `files=...` list.
            # We'll use the list form.
            pass

        multipart = []
        for k, v in fields.items():
            multipart.append((k, (None, str(v))))

        if files_b64:
            for f in files_b64:
                name = f.get("name")
                b64 = f.get("bytes_base64") or f.get("bytesBase64")
                ctype = f.get("content_type") or "application/octet-stream"
                if not name or not b64:
                    raise ValidationError("files items require: name, bytes_base64")
                try:
                    raw = base64.b64decode(b64)
                except Exception as e:
                    raise ValidationError(f"invalid base64 for file {name}") from e
                multipart.append(("files", (name, raw, ctype)))

        resp = self.request("POST", path, files=multipart)  # type: ignore[arg-type]
        if not resp.content:
            return {"ok": True}
        try:
            return resp.json()
        except Exception:
            return {"ok": True, "raw": resp.text}

    def close(self) -> None:
        self._client.close()
