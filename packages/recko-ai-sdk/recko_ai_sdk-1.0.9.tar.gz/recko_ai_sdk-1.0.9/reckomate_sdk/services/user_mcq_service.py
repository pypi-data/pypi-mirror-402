from typing import Dict, Any, List

from ..exceptions import ReckomateAPIError


class UserMCQService:
    """
    SDK proxy for User & Admin MCQ operations.

    Backend file:
    - app/services/user_mcq_service.py

    IMPORTANT:
    - phone (user) identity is derived from USER JWT
    - admin identity is derived from ADMIN JWT
    - SDK must NEVER send phone or admin_id explicitly
    """

    def __init__(self, client):
        self.client = client

    # ============================================================
    # USER → Get assigned MCQs
    # ============================================================

    def get_visible_mcqs(self) -> List[Dict[str, Any]]:
        """
        Get list of MCQs assigned to the logged-in user.

        Backend:
        GET /user/mcqs
        """

        response = self.client.get("/user/mcqs")
        return self._handle_response(response)

    # ============================================================
    # USER → Start / Resume MCQ
    # ============================================================

    def start_mcq(self, *, mcq_id: str) -> Dict[str, Any]:
        """
        Start or resume an MCQ test.

        Backend:
        POST /user/startMcqTest
        """

        response = self.client.post(
            "/user/startMcqTest",
            json={"mcq_id": mcq_id}
        )

        return self._handle_response(response)

    # ============================================================
    # USER → Submit MCQ
    # ============================================================

    def submit_mcq(
        self,
        *,
        mcq_id: str,
        answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Submit MCQ answers.

        answers format:
        {
            "0": "A",
            "1": "C",
            "2": "B"
        }

        Backend:
        POST /user/submitMcqTest
        """

        response = self.client.post(
            "/user/submitMcqTest",
            json={
                "mcq_id": mcq_id,
                "answers": answers
            }
        )

        return self._handle_response(response)

    # ============================================================
    # ADMIN → Get all MCQ results
    # ============================================================

    def get_all_results(self) -> List[Dict[str, Any]]:
        """
        Get all MCQ submissions.

        Backend:
        GET /user/admin/results

        Requires:
        - ADMIN access token
        """

        response = self.client.get("/user/admin/results")
        return self._handle_response(response)

    # ============================================================
    # INTERNAL
    # ============================================================

    def _handle_response(self, response):
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
                or "User MCQ API error",
                payload=data
            )

        return data
