from __future__ import annotations

from typing import Any, Dict

from ..core.client import CoreClient


class PhoneNumbers:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def list(
        self, *, page_size: int = 20, page_token: str | None = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._client.request("GET", "/v1/phone-numbers", params=params)

    def get(self, phone_number_id: str) -> Dict[str, Any]:
        return self._client.request("GET", f"/v1/phone-numbers/{phone_number_id}")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request("POST", "/v1/phone-numbers", json=payload)

    def update(self, phone_number_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request(
            "PATCH", f"/v1/phone-numbers/{phone_number_id}", json=payload
        )

    def delete(self, phone_number_id: str) -> None:
        self._client.request("DELETE", f"/v1/phone-numbers/{phone_number_id}")
