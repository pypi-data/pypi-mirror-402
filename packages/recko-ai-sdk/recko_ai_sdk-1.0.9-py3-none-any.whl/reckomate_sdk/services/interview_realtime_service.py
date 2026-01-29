class InterviewRealtimeService:
    """
    SDK helper for Interview WebSocket connection.

    IMPORTANT:
    - SDK does NOT send phone or user_id
    - Identity is derived from JWT on backend
    - SDK only constructs WebSocket URL
    """

    def __init__(self, base_ws_url: str, access_token: str):
        self.base_ws_url = base_ws_url.rstrip("/")
        self.access_token = access_token

    def get_ws_url(self, *, mcq_id: str) -> str:
        """
        Build WebSocket URL for interview session.

        Backend endpoint:
        ws://<host>/ws/interview/{mcq_id}?token=<JWT>

        Example:
        ws://52.87.148.155:8000/ws/interview/65fa... ?token=eyJhb...
        """

        return (
            f"{self.base_ws_url}/ws/interview/{mcq_id}"
            f"?token={self.access_token}"
        )
