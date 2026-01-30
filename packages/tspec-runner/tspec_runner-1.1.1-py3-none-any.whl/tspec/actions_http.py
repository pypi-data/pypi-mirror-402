from __future__ import annotations

import json
from typing import Any, Dict, Optional

import urllib.error
import urllib.request

from .errors import ExecutionError


def http_request(args: Dict[str, Any]) -> Dict[str, Any]:
    method = (args.get("method") or "GET").upper()
    url = args.get("url")
    if not url:
        raise ExecutionError("http.request requires 'url'.")
    headers = dict(args.get("headers") or {})
    body = args.get("body")
    data: Optional[bytes] = None
    if isinstance(body, dict):
        data = json.dumps(body).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    elif isinstance(body, str):
        data = body.encode("utf-8")
    timeout = float(args.get("timeout", 10))
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body_text = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body_text = exc.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        raise ExecutionError(f"http.request failed: {exc}") from exc
    expect_status = args.get("expect_status")
    if expect_status is not None:
        if isinstance(expect_status, list):
            valid = status in expect_status
        else:
            valid = status == int(expect_status)
        if not valid:
            raise ExecutionError(f"http.request status {status} != expected {expect_status}")
    return {"status": status, "body": body_text}
