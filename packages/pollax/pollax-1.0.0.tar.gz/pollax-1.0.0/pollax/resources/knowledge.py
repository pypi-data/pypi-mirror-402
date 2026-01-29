"""Knowledge resource"""

from typing import List, Optional, TYPE_CHECKING, Union, BinaryIO
from ..models import KnowledgeDocument

if TYPE_CHECKING:
    from ..client import Pollax


class KnowledgeResource:
    """Knowledge Base API resource"""

    def __init__(self, client: "Pollax"):
        self._client = client

    def upload(
        self,
        name: str,
        file: Optional[Union[BinaryIO, bytes]] = None,
        content: Optional[str] = None,
        url: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> KnowledgeDocument:
        """Upload a document to the knowledge base."""
        files = {}
        data = {"name": name}

        if file:
            files["file"] = file
        if content:
            data["content"] = content
        if url:
            data["url"] = url
        if doc_type:
            data["type"] = doc_type

        response = self._client.request("POST", "/api/v1/knowledge", files=files if files else None, params=data)
        return KnowledgeDocument(**response)

    def list(self) -> List[KnowledgeDocument]:
        """List all knowledge documents."""
        response = self._client.request("GET", "/api/v1/knowledge")
        return [KnowledgeDocument(**item) for item in response]

    def retrieve(self, document_id: str) -> KnowledgeDocument:
        """Get a single document by ID."""
        response = self._client.request("GET", f"/api/v1/knowledge/{document_id}")
        return KnowledgeDocument(**response)

    def delete(self, document_id: str) -> dict:
        """Delete a document."""
        return self._client.request("DELETE", f"/api/v1/knowledge/{document_id}")

    def search(self, query: str, limit: int = 5) -> dict:
        """Search the knowledge base."""
        return self._client.request(
            "POST",
            "/api/v1/knowledge/search",
            json={"query": query, "limit": limit},
        )
