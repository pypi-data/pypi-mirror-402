from __future__ import annotations

from typing import Any, Dict, Sequence

from ..core.client import CoreClient


class Calls:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def create_web_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request("POST", "/v1/calls/create-web-call", json=payload)

    def create_public_web_call(
        self, *, ai_agent_id: str, shared_key: str
    ) -> Dict[str, Any]:
        params = {"ai_agent_id": ai_agent_id, "shared_key": shared_key}
        return self._client.request(
            "GET", "/v1/calls/public/create-web-call", params=params
        )

    def dial_outbound_phone_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request(
            "POST", "/v1/calls/dial-outbound-phone-call", json=payload
        )

    def get(self, call_id: str) -> Dict[str, Any]:
        return self._client.request("GET", f"/v1/calls/{call_id}")

    def list(
        self,
        *,
        ai_agent_ids: Sequence[str] | None = None,
        start_time_before: str | None = None,
        start_time_after: str | None = None,
        end_time_before: str | None = None,
        end_time_after: str | None = None,
        sort_direction: str = "desc",
        page_size: int = 100,
        page_token: str | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "sort_direction": sort_direction,
            "page_size": page_size,
        }
        if ai_agent_ids:
            params["ai_agent_ids"] = ai_agent_ids
        if start_time_before:
            params["start_time_before"] = start_time_before
        if start_time_after:
            params["start_time_after"] = start_time_after
        if end_time_before:
            params["end_time_before"] = end_time_before
        if end_time_after:
            params["end_time_after"] = end_time_after
        if page_token:
            params["page_token"] = page_token
        return self._client.request("GET", "/v1/calls", params=params)
