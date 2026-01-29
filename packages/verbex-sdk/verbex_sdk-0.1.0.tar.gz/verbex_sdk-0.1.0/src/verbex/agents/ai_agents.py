from __future__ import annotations

from typing import Any, Dict

from ..core.client import CoreClient


class AIAgents:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def list(
        self, *, page_size: int = 20, page_token: str | None = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._client.request("GET", "/v2/ai-agents", params=params)

    def get(self, agent_id: str) -> Dict[str, Any]:
        return self._client.request("GET", f"/v2/ai-agents/{agent_id}")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request("POST", "/v2/ai-agents", json=payload)

    def update(self, agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request("PUT", f"/v2/ai-agents/{agent_id}", json=payload)

    def delete(self, agent_id: str) -> None:
        self._client.request("DELETE", f"/v2/ai-agents/{agent_id}")
