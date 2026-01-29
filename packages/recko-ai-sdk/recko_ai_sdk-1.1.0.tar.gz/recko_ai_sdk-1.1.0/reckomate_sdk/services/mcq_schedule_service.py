from typing import Dict, Any
from datetime import datetime

from ..exceptions import ReckomateAPIError


class MCQScheduleService:
    """
    SDK proxy for MCQ scheduling APIs.

    Backend services:
    - schedule_mcq_for_excel
    - get_all_scheduled_mcqs_with_status

    IMPORTANT:
    - admin_id is derived from JWT via gateway_guard
    - SDK must NEVER send admin_id explicitly
    """

    def __init__(self, client):
        self.client = client

    # --------------------------------------------------
    # Schedule MCQ for Excel upload
    # --------------------------------------------------
    def schedule_mcq(
        self,
        *,
        mcq_id: str,
        excel_upload_id: str,
        scheduled_start_time: datetime,
        break_time: int = 10,
        interview_duration: int = 20
    ) -> Dict[str, Any]:
        """
        Schedule an MCQ test for users from an Excel upload.

        Backend:
        POST /admin/mcq/schedule

        Payload:
        {
          "mcq_id": str,
          "excel_upload_id": str,
          "scheduled_start_time": ISO datetime,
          "break_time": int,
          "interview_duration": int
        }
        """

        payload = {
            "mcq_id": mcq_id,
            "excel_upload_id": excel_upload_id,
            "scheduled_start_time": scheduled_start_time.isoformat(),
            "break_time": break_time,
            "interview_duration": interview_duration
        }

        response = self.client.post(
            "/admin/mcq/schedule",
            json=payload
        )

        return self._handle_response(response)

    # --------------------------------------------------
    # Get all scheduled MCQs (live / upcoming / completed)
    # --------------------------------------------------
    def get_all_scheduled_mcqs(self) -> Dict[str, Any]:
        """
        Get all scheduled MCQs with status for the logged-in admin.

        Backend:
        GET /admin/mcq/schedules

        Returns:
        {
          "counts": {
            "live": int,
            "upcoming": int,
            "completed": int
          },
          "live": [...],
          "upcoming": [...],
          "completed": [...]
        }
        """

        response = self.client.get(
            "/admin/mcq/schedules"
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
