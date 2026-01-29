# reckomate_sdk/services/excel_service.py

from typing import Any, Dict
from pathlib import Path

from ..exceptions import ReckomateAPIError


class ExcelService:
    """
    SDK proxy for Admin Excel upload APIs

    NOTE:
    - Admin identity is derived from JWT via gateway_guard
    - SDK does NOT send admin_id explicitly
    """

    def __init__(self, client):
        self.client = client

    def upload_excel(self, file_path: str) -> Dict[str, Any]:
        """
        Upload Excel file to backend for processing.

        Backend:
        POST /admin/uploadExcel

        Args:
            file_path: Path to .xls or .xlsx file

        Returns:
            {
              "document_id": str,
              "total_contacts": int
            }
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix not in (".xls", ".xlsx"):
            raise ValueError("Only .xls or .xlsx files are allowed")

        with open(path, "rb") as f:
            files = {
                "file": (
                    path.name,
                    f,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }

            response = self.client.post(
                "/admin/uploadExcel",
                files=files
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
                message=data.get("detail") or data.get("message") or "API Error",
                payload=data
            )

        return data
