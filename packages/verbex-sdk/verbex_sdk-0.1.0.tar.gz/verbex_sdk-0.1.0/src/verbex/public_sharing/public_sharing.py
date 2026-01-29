from __future__ import annotations

from typing import Any, Dict

from ..core.client import CoreClient


class PublicSharing:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def create(self, ai_agent_id: str) -> Dict[str, Any]:
        payload = {"ai_agent_id": ai_agent_id}
        return self._client.request("POST", "/v1/public-sharing", json=payload)

    def get(self, ai_agent_id: str) -> Dict[str, Any]:
        return self._client.request("GET", f"/v1/public-sharing/{ai_agent_id}")

    def delete(self, share_id: str) -> None:
        self._client.request("DELETE", f"/v1/public-sharing/{share_id}")
