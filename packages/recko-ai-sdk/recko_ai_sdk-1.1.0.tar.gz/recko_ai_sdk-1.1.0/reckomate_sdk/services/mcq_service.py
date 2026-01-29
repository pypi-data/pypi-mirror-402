from typing import Dict, Any, List

from ..exceptions import ReckomateAPIError


class MCQService:
    """
    SDK proxy for Admin MCQ APIs.

    Backend file:
    - app/services/mcq_service.py

    IMPORTANT:
    - admin_id is derived from JWT via gateway_guard
    - SDK must NEVER send admin_id explicitly
    """

    def __init__(self, client):
        self.client = client

    # ============================================================
    # GENERATE + STORE MCQs
    # ============================================================

    def generate_mcq(
        self,
        *,
        file_id: str,
        title: str,
        difficulty: str,
        time_limit: int,
        number_of_questions: int,
        choices: int,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Generate and store MCQs from ingested content.

        Backend:
        POST /admin/generate-mcq
        """

        payload = {
            "file_id": file_id,
            "title": title,
            "difficulty": difficulty,
            "time_limit": time_limit,
            "number_of_questions": number_of_questions,
            "choices": choices,
            "language": language
        }

        response = self.client.post(
            "/admin/generate-mcq",
            json=payload
        )

        return self._handle_response(response)

    # ============================================================
    # GET MCQ TITLES (ADMIN)
    # ============================================================

    def get_mcq_titles(self) -> List[Dict[str, Any]]:
        """
        Get all MCQ titles created by the logged-in admin.

        Backend:
        GET /admin/mcqs/titles
        """

        response = self.client.get(
            "/admin/mcqs/titles"
        )

        return self._handle_response(response)

    # ============================================================
    # GET MCQ QUESTIONS (ADMIN)
    # ============================================================

    def get_mcq_questions(self) -> List[Dict[str, Any]]:
        """
        Get all MCQs with full question details for admin.

        Backend:
        GET /admin/mcqs/questions
        """

        response = self.client.get(
            "/admin/mcqs/questions"
        )

        return self._handle_response(response)

    # ============================================================
    # GET MCQ RESULTS (ADMIN)
    # ============================================================

    def get_mcq_results(self, mcq_id: str) -> List[Dict[str, Any]]:
        """
        Get results for a specific MCQ (admin-only).

        Backend:
        GET /admin/mcq/results/{mcq_id}
        """

        response = self.client.get(
            f"/admin/mcq/results/{mcq_id}"
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
