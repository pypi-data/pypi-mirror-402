# reckomate_sdk/services/linktestwithphone_service.py

from typing import Dict, Any

from ..exceptions import ReckomateAPIError


class LinkTestWithPhoneService:
    """
    SDK proxy for MCQ assignment & leaderboard APIs.

    Backend services:
    - Assign MCQ to phones (via Excel upload)
    - Fetch MCQ leaderboard

    NOTE:
    - Admin identity is derived from JWT via gateway_guard
    - SDK does NOT send admin_id explicitly
    """

    def __init__(self, client):
        self.client = client

    # --------------------------------------------------
    # Assign MCQ to phones using Excel upload
    # --------------------------------------------------
    def assign_mcq(
        self,
        mcq_id: str,
        excel_upload_id: str
    ) -> Dict[str, Any]:
        """
        Assign MCQ to phone numbers from Excel upload.

        Backend:
        POST /admin/mcq/assign

        Payload:
        {
          "mcq_id": str,
          "excel_upload_id": str
        }
        """

        payload = {
            "mcq_id": mcq_id,
            "excel_upload_id": excel_upload_id
        }

        response = self.client.post(
            "/admin/mcq/assign",
            json=payload
        )

        return self._handle_response(response)

    # --------------------------------------------------
    # Get MCQ leaderboard
    # --------------------------------------------------
    def get_leaderboard(self, mcq_id: str) -> Dict[str, Any]:
        """
        Get leaderboard for a MCQ.

        Backend:
        GET /admin/mcq/leaderboard/{mcq_id}
        """

        response = self.client.get(
            f"/admin/mcq/leaderboard/{mcq_id}"
        )

        return self._handle_response(response)

    # --------------------------------------------------
    # INTERNAL
    # --------------------------------------------------
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
                message=data.get("detail") or data.get("message") or "API Error",
                payload=data
            )

        return data
