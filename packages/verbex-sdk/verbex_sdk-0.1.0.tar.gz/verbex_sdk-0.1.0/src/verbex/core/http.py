from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from .errors import VerbexAPIError


class HTTPClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        timeout: int | float,
    ) -> None:
        self.api_key = api_key or os.getenv("VERBEX_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Pass api_key or set VERBEX_API_KEY.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def close(self) -> None:
        self.session.close()

    def _headers(
        self, extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        request_headers: Dict[str, str] | None = None
        if headers is not None:
            request_headers = headers
        elif json is not None:
            request_headers = {"Content-Type": "application/json"}
        response = self.session.request(
            method,
            url,
            headers=self._headers(request_headers),
            params=params,
            json=json,
            data=data,
            files=files,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise VerbexAPIError(
                response.status_code,
                f"Verbex API error {response.status_code}",
                response.text,
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()
