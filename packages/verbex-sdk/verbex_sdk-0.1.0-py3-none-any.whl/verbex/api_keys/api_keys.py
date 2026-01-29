from __future__ import annotations

from typing import Any, Dict

from ..core.client import CoreClient


class APIKeys:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def list(
        self, *, page_size: int = 20, page_token: str | None = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._client.request("GET", "/v1/api-keys", params=params)

    def get(self, key_id: str) -> Dict[str, Any]:
        return self._client.request("GET", f"/v1/api-keys/{key_id}")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request("POST", "/v1/api-keys", json=payload)

    def revoke(self, key_id: str) -> Dict[str, Any]:
        return self._client.request("POST", f"/v1/api-keys/{key_id}/revoke")
