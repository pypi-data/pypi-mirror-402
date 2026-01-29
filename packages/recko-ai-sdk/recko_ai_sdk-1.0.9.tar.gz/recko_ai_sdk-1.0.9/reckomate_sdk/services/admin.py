from pathlib import Path
from typing import Dict, List

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class AdminService:
    """
    Admin SDK Service

    Handles:
    - Admin registration
    - Admin login
    - Forgot / reset password
    - Document / audio / video ingest
    - Fetch uploaded files history

    NOTE:
    - admin_id is NEVER sent from SDK
    - Identity is derived from JWT via gateway_guard
    """

    def __init__(self, client: ReckomateClient):
        self.client = client

    # ============================================================
    # AUTH
    # ============================================================

    def register(self, full_name: str, email: str, password: str) -> Dict:
        payload = {
            "full_name": full_name,
            "email": email,
            "password": password
        }

        response = self.client.post("/admin/register", json=payload)
        return self._handle_response(response)

    def login(self, email: str, password: str) -> Dict:
        payload = {
            "email": email,
            "password": password
        }

        response = self.client.post("/admin/login", json=payload)
        return self._handle_response(response)

    # ============================================================
    # PASSWORD RECOVERY
    # ============================================================

    def forgot_password(self, email: str) -> Dict:
        response = self.client.post(
            "/admin/forgot-password",
            json={"email": email}
        )
        return self._handle_response(response)

    def verify_forgot_otp(self, email: str, otp: str) -> Dict:
        response = self.client.post(
            "/admin/verify-forgot-otp",
            json={"email": email, "otp": otp}
        )
        return self._handle_response(response)

    def reset_password(self, email: str, new_password: str) -> Dict:
        response = self.client.post(
            "/admin/reset-password",
            json={
                "email": email,
                "new_password": new_password
            }
        )
        return self._handle_response(response)

    # ============================================================
    # INGEST
    # ============================================================

    def ingest_file(self, file_path: str) -> Dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            files = {
                "file": (path.name, f)
            }

            response = self.client.post(
                "/admin/ingest",
                files=files
            )

        return self._handle_response(response)

    # ============================================================
    # FILE HISTORY (NEW)
    # ============================================================

    def get_uploaded_files(self) -> List[Dict]:
        """
        Get all uploaded files by the logged-in admin.

        Backend:
        GET /admin/uploads
        """

        response = self.client.get("/admin/uploads")
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
                or "API Error",
                payload=data
            )

        return data
