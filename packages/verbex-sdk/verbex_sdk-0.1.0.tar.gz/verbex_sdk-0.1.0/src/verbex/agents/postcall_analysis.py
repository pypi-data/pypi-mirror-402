from __future__ import annotations

from typing import Any, Dict

from ..core.client import CoreClient


class PostCallAnalysis:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def get(self, ai_agent_id: str) -> Dict[str, Any]:
        return self._client.request(
            "GET", f"/v2/ai-agents/{ai_agent_id}/postcall-analysis"
        )

    def create(self, ai_agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request(
            "POST",
            f"/v2/ai-agents/{ai_agent_id}/postcall-analysis",
            json=payload,
        )

    def update(self, ai_agent_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request(
            "PUT",
            f"/v2/ai-agents/{ai_agent_id}/postcall-analysis",
            json=payload,
        )

    def delete(self, ai_agent_id: str) -> None:
        self._client.request("DELETE", f"/v2/ai-agents/{ai_agent_id}/postcall-analysis")

    def results(self, ai_agent_id: str, call_id: str) -> Dict[str, Any]:
        return self._client.request(
            "GET",
            f"/v2/ai-agents/{ai_agent_id}/postcall-analysis/results/{call_id}",
        )
