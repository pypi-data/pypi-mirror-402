from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..core.client import CoreClient


class KnowledgeBases:
    def __init__(self, client: CoreClient) -> None:
        self._client = client

    def list(
        self, *, page_size: int = 20, page_token: str | None = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._client.request("GET", "/v2/knowledge-bases", params=params)

    def get(self, kb_id: str) -> Dict[str, Any]:
        return self._client.request("GET", f"/v2/knowledge-bases/{kb_id}")

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request("POST", "/v2/knowledge-bases", json=payload)

    def update(self, kb_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._client.request("PUT", f"/v2/knowledge-bases/{kb_id}", json=payload)

    def delete(self, kb_id: str) -> None:
        self._client.request("DELETE", f"/v2/knowledge-bases/{kb_id}")

    def fetch_website_sitemap(self, url: str) -> Dict[str, Any]:
        data = {"url": url}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return self._client.request(
            "POST",
            "/v2/knowledge-bases/website/sitemap",
            data=data,
            headers=headers,
        )

    def add_website_documents(
        self, kb_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._client.request(
            "POST",
            f"/v2/knowledge-bases/{kb_id}/documents/website",
            json=payload,
        )

    def add_files_documents(
        self,
        kb_id: str,
        files: Iterable[Tuple[str, Tuple[str, Any]]],
        document_languages: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if document_languages:
            data["document_languages"] = document_languages
        return self._client.request(
            "POST",
            f"/v2/knowledge-bases/{kb_id}/documents/files",
            data=data,
            files=dict(files),
        )

    def get_document_status(self, kb_id: str, document_id: str) -> Dict[str, Any]:
        return self._client.request(
            "GET",
            f"/v2/knowledge-bases/{kb_id}/documents/{document_id}/status",
        )

    def delete_document(self, kb_id: str, document_id: str) -> None:
        self._client.request(
            "DELETE",
            f"/v2/knowledge-bases/{kb_id}/documents/{document_id}",
        )

    def list_documents(
        self,
        kb_id: str,
        *,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self._client.request(
            "GET", f"/v2/knowledge-bases/{kb_id}/documents", params=params
        )
