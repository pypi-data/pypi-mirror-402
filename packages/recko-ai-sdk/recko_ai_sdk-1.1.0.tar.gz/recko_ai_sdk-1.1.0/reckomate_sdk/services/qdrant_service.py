from typing import Dict, Any

from ..exceptions import ReckomateAPIError


class QdrantService:
    """
    SDK proxy for Qdrant-related backend APIs.

    Backend file:
    - app/services/qdrant_service.py

    IMPORTANT:
    - SDK does NOT talk to Qdrant directly
    - admin_id is derived from JWT via gateway_guard
    """

    def __init__(self, client):
        self.client = client

    # ============================================================
    # GET CONTENT BY FILE ID
    # ============================================================

    def get_content_by_file_id(
        self,
        *,
        file_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Retrieve stored text content for a file.

        Backend:
        GET /admin/qdrant/content/{file_id}?limit=50
        """

        response = self.client.get(
            f"/admin/qdrant/content/{file_id}",
            params={"limit": limit}
        )

        return self._handle_response(response)

    # ============================================================
    # SUMMARIZE MATERIAL (INTERVIEW)
    # ============================================================

    def summarize_material(self, file_id: str) -> Dict[str, Any]:
        """
        Generate a summary of uploaded material for interview questions.

        Backend:
        GET /admin/qdrant/summarize/{file_id}
        """

        response = self.client.get(
            f"/admin/qdrant/summarize/{file_id}"
        )

        return self._handle_response(response)

    # ============================================================
    # INTERNAL
    # ============================================================

    def _handle_response(self, response):
        """
        Unified response handler.
        """
        try:
            data = response.json()
        except Exception:
            raise ReckomateAPIError(
                status_code=response.status_code,
                message="Invalid JSON response from server"
            )

        if response.status_code >= 400:
            raise ReckomateAPIError(
                status_code=response.status_code,
                message=data.get("detail")
                or data.get("message")
                or "API Error",
                payload=data
            )

        return data
