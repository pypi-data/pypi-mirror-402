from __future__ import annotations

from typing import Any, Dict

from ..core.client import CoreClient


class BuiltinTools:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def list(
        self,
        ai_agent_id: str,
        *,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._client.request(
            "GET",
            f"/v2/ai-agents/{ai_agent_id}/builtin-tools",
            params=params,
        )

    def get(self, ai_agent_id: str, tool_id: str) -> Dict[str, Any]:
        return self._client.request(
            "GET",
            f"/v2/ai-agents/{ai_agent_id}/builtin-tools/{tool_id}",
        )

    def create(self, ai_agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request(
            "POST",
            f"/v2/ai-agents/{ai_agent_id}/builtin-tools",
            json=payload,
        )

    def update(
        self, ai_agent_id: str, tool_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._client.request(
            "PUT",
            f"/v2/ai-agents/{ai_agent_id}/builtin-tools/{tool_id}",
            json=payload,
        )

    def delete(self, ai_agent_id: str, tool_id: str) -> None:
        self._client.request(
            "DELETE", f"/v2/ai-agents/{ai_agent_id}/builtin-tools/{tool_id}"
        )
