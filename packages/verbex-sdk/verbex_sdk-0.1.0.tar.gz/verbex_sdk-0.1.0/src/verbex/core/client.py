from __future__ import annotations

from typing import Any, Dict, Optional

from .http import HTTPClient


class CoreClient:
    def __init__(
        self, api_key: str | None, base_url: str, timeout: int | float
    ) -> None:
        self._http = HTTPClient(api_key=api_key, base_url=base_url, timeout=timeout)

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
        return self._http.request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )

    def close(self) -> None:
        self._http.close()
