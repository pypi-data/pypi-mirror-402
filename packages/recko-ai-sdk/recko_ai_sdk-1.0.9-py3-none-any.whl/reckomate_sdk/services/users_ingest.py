from pathlib import Path
from typing import Dict

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class UserIngestService:
    """
    User Ingest SDK Service

    Handles:
    - File ingest
    - Website ingest
    - YouTube ingest

    IMPORTANT:
    - user_id is derived from USER JWT via gateway_guard
    - SDK must NEVER send user_id explicitly
    """

    def __init__(self, client: ReckomateClient):
        self.client = client

    # ============================================================
    # FILE INGEST
    # ============================================================

    def ingest_file(self, file_path: str) -> Dict:
        """
        Upload & ingest a file for the logged-in user.

        Backend:
        POST /users/ingest
        """

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            response = self.client.post(
                "/users/ingest",
                files={"file": (path.name, f)}
            )

        return self._handle_response(response)

    # ============================================================
    # WEBSITE INGEST
    # ============================================================

    def ingest_website(self, *, url: str) -> Dict:
        """
        Ingest website content.

        Backend:
        POST /users/ingest/website
        """

        response = self.client.post(
            "/users/ingest/website",
            json={"url": url}
        )

        return self._handle_response(response)

    # ============================================================
    # YOUTUBE INGEST
    # ============================================================

    def ingest_youtube(self, *, url: str) -> Dict:
        """
        Ingest YouTube transcript.

        Backend:
        POST /users/ingest/youtube
        """

        response = self.client.post(
            "/users/ingest/youtube",
            json={"url": url}
        )

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
                or "User ingest API error",
                payload=data
            )

        return data
