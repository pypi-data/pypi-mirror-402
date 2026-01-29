from typing import Dict, Any, Optional

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class QuestionService:
    """
    Question SDK Service

    Handles:
    - Question generation (MCQ / True-False / Short / Long Answer)

    IMPORTANT:
    - user_id is derived from auth / websocket context on backend
    - SDK must NEVER send user_id explicitly
    """

    def __init__(self, client: ReckomateClient):
        self.client = client

    # ============================================================
    # GENERATE QUESTIONS
    # ============================================================

    def generate(
        self,
        *,
        file_id: str,
        num_questions: int,
        difficulty: str,
        language: str,
        question_type: str,
        timer: int,
        num_choices: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate questions for a user.

        Backend:
        POST /questions/generate

        Supported question_type values:
        - "MCQ"
        - "True/False"
        - "Short Answer"
        - "Long Answer"

        Payload example:
        {
            "file_id": "...",
            "num_questions": 5,
            "difficulty": "medium",
            "language": "English",
            "question_type": "MCQ",
            "num_choices": 4,
            "timer": 60
        }
        """

        payload = {
            "file_id": file_id,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "language": language,
            "question_type": question_type,
            "timer": timer
        }

        # Only required for MCQ
        if question_type == "MCQ":
            if not num_choices:
                raise ValueError("num_choices is required for MCQ questions")
            payload["num_choices"] = num_choices

        response = self.client.post(
            "/questions/generate",
            json=payload
        )

        return self._handle_response(response)

    # ============================================================
    # INTERNAL RESPONSE HANDLER
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
                or "Question generation API error",
                payload=data
            )

        return data
