from __future__ import annotations

from typing import Any, Dict

from ..core.client import CoreClient


class PromptGeneration:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def generate_prompt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request(
            "POST", "/v1/prompt-generation/prompt/generate", json=payload
        )
