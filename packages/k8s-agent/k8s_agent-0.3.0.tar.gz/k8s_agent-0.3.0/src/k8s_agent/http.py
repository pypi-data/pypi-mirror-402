from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass
class APIError(RuntimeError):
    status_code: int
    message: str
    payload: Optional[dict[str, Any]] = None

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"


def _join(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = "/" + path.lstrip("/")
    return base + path


class K8sVMgrAPI:
    def __init__(self, api_url: str, access_token: str = ""):
        self.api_url = api_url.rstrip("/")
        self.access_token = access_token

    def request(self, method: str, path: str, *, json_body: Any = None, timeout: int = 20) -> dict[str, Any]:
        url = _join(self.api_url, path)
        headers = {"Accept": "application/json"}
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        r = requests.request(method, url, headers=headers, json=json_body, timeout=timeout)
        try:
            body = r.json()
        except Exception:
            body = None

        if r.status_code >= 400:
            msg = ""
            if isinstance(body, dict):
                # your API seems to use {"error": "..."} for errors
                msg = str(body.get("error") or body.get("message") or body)
            if not msg:
                msg = r.text or "request failed"
            raise APIError(r.status_code, msg, payload=body if isinstance(body, dict) else None)

        if not isinstance(body, dict):
            raise APIError(r.status_code, "Invalid JSON response", payload=None)
        return body


