from typing import Dict, Optional
from pathlib import Path

from ..client import ReckomateClient
from ..exceptions import ReckomateAPIError


class UserService:
    """
    SDK wrapper for all /user APIs

    IMPORTANT:
    - user identity comes ONLY from JWT
    - SDK must NEVER send user_id for self actions
    """

    def __init__(self, client: ReckomateClient):
        self.client = client

    # ======================================================
    # 🔐 AUTH
    # ======================================================

    def login(self, *, email: str | None = None, phone: str | None = None) -> Dict:
        return self._handle(
            self.client.post("/user/login", json={"email": email, "phone": phone})
        )

    def register(self, *, email: str | None = None, phone: str | None = None) -> Dict:
        return self._handle(
            self.client.post("/user/register", json={"email": email, "phone": phone})
        )

    def resend_otp(self, *, email: str | None = None, phone: str | None = None) -> Dict:
        return self._handle(
            self.client.post("/user/resend-otp", json={"email": email, "phone": phone})
        )

    def verify_otp(
        self,
        *,
        otp: str,
        email: str | None = None,
        phone: str | None = None,
        fcm_token: str | None = None,
    ) -> Dict:
        return self._handle(
            self.client.post(
                "/user/verify-otp",
                json={
                    "otp": otp,
                    "email": email,
                    "phone": phone,
                    "fcm_token": fcm_token,
                },
            )
        )

    # ======================================================
    # 👤 PROFILE (SELF)
    # ======================================================

    def get_my_profile(self) -> Dict:
        """
        GET /user/profile
        (JWT required)
        """
        return self._handle(
            self.client.get("/user/profile")
        )

    def update_my_profile(
        self,
        *,
        name: str,
        email: str,
        phone: str,
        profile_image_path: Optional[str] = None,
    ) -> Dict:
        """
        POST /user/profile
        (JWT required)
        """

        data = {
            "name": name,
            "email": email,
            "phone": phone,
        }

        files = None
        if profile_image_path:
            p = Path(profile_image_path)
            files = {
                "profile_image": (p.name, open(p, "rb"), "application/octet-stream")
            }

        return self._handle(
            self.client.post("/user/profile", data=data, files=files)
        )

    # ======================================================
    # 👤 PROFILE (ADMIN ONLY)
    # ======================================================

    def admin_update_user_profile(
        self,
        *,
        user_id: str,
        name: str,
        email: str,
        phone: str,
        profile_image_path: Optional[str] = None,
    ) -> Dict:
        """
        PUT /user/profile/edit/{user_id}
        (ADMIN token required)
        """

        data = {
            "name": name,
            "email": email,
            "phone": phone,
        }

        files = None
        if profile_image_path:
            p = Path(profile_image_path)
            files = {
                "profile_image": (p.name, open(p, "rb"), "application/octet-stream")
            }

        return self._handle(
            self.client.put(
                f"/user/profile/edit/{user_id}",
                data=data,
                files=files
            )
        )

    # ======================================================
    # 🔧 INTERNAL RESPONSE HANDLER
    # ======================================================

    def _handle(self, response):
        try:
            data = response.json()
        except Exception:
            raise ReckomateAPIError(
                response.status_code,
                "Invalid JSON response from server"
            )

        if response.status_code >= 400:
            raise ReckomateAPIError(
                response.status_code,
                data.get("message")
                or data.get("detail")
                or "User API error",
                data,
            )

        return data
