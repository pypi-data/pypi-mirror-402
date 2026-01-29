from typing import Dict, Any


class UserTestService:
    """
    SDK proxy for User Test APIs.

    IMPORTANT:
    - user_id is derived ONLY from JWT
    - SDK must NEVER send user_id
    """

    def __init__(self, client):
        self.client = client

    # --------------------------------------------------
    # USER → Start Test
    # POST /user-test/start
    # --------------------------------------------------
    def start_test(
        self,
        *,
        test_id: str,
        timer: int
    ) -> Dict[str, Any]:
        """
        Start a user test.

        Payload sent:
        {
            "test_id": "...",
            "timer": 30
        }
        """

        payload = {
            "test_id": test_id,
            "timer": timer
        }

        return self.client.post(
            "/user-test/start",
            json=payload
        )

    # --------------------------------------------------
    # USER → Submit Test
    # POST /user-test/submit
    # --------------------------------------------------
    def submit_test(
        self,
        *,
        test_id: str,
        arrayofMcq: list
    ) -> Dict[str, Any]:
        """
        Submit test answers.

        arrayofMcq example:
        [
            {
                "question": "What is Python?",
                "selected_answer": "A"
            }
        ]
        """

        payload = {
            "test_id": test_id,
            "arrayofMcq": arrayofMcq
        }

        return self.client.post(
            "/user-test/submit",
            json=payload
        )

    # --------------------------------------------------
    # USER → Check Test Status
    # GET /user-test/status/{test_id}
    # --------------------------------------------------
    def check_test_status(
        self,
        *,
        test_id: str
    ) -> Dict[str, Any]:
        """
        Check test status or auto-submit when time expires.
        JWT user is inferred by backend.
        """

        return self.client.get(
            f"/user-test/status/{test_id}"
        )
