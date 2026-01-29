"""
Reckomate SDK
~~~~~~~~~~~~~

Python SDK for interacting with Reckomate backend services.
"""

from .client import ReckomateClient

# =========================
# Core Services
# =========================
from .services.admin import AdminService
from .services.users import UserService
from .services.users_ingest import UsersIngestService
from .services.question import QuestionService

# =========================
# Excel & MCQ Services
# =========================
from .services.excel_service import ExcelService
from .services.linktestwithphone_service import LinkTestWithPhoneService
from .services.mcq_schedule_service import MCQScheduleService
from .services.mcq_service import MCQService
from .services.qdrant_service import QdrantService
from .services.leaderboard_service import LeaderboardService

# =========================
# Interview Services
# =========================
from .services.interview_logic_service import InterviewLogicService
from .services.interview_realtime_service import InterviewRealtimeService
from .services.interview_scheduler_service import InterviewSchedulerService

# =========================
# User MCQ & Test Services
# =========================
from .services.user_mcq_service import UserMCQService
from .services.usertest_service import UserTestService


class ReckomateSDK:
    """
    Main SDK entry point.

    Aggregates all backend services
    and exposes them via a single SDK object.
    """

    def __init__(self, base_url: str, token: str | None = None):
        self._client = ReckomateClient(
            base_url=base_url,
            token=token
        )

        # =========================
        # Admin & User
        # =========================
        self.admin = AdminService(self._client)
        self.users = UserService(self._client)
        self.users_ingest = UsersIngestService(self._client)

        # =========================
        # Questions & Content
        # =========================
        self.questions = QuestionService(self._client)
        self.qdrant = QdrantService(self._client)

        # =========================
        # Excel & MCQ Flow
        # =========================
        self.excel = ExcelService(self._client)
        self.mcq = MCQService(self._client)
        self.mcq_schedule = MCQScheduleService(self._client)
        self.link_test = LinkTestWithPhoneService(self._client)
        self.leaderboard = LeaderboardService(self._client)

        # =========================
        # Interview Flow
        # =========================
        self.interview_logic = InterviewLogicService(self._client)
        self.interview_realtime = InterviewRealtimeService(self._client)
        self.interview_scheduler = InterviewSchedulerService(self._client)

        # =========================
        # User-facing MCQ & Tests
        # =========================
        self.user_mcq = UserMCQService(self._client)
        self.user_test = UserTestService(self._client)

    # =========================
    # Token Management
    # =========================
    def set_token(self, token: str):
        self._client.set_token(token)


__all__ = [
    "ReckomateSDK",
    "ReckomateClient",

    # Core
    "AdminService",
    "UserService",
    "UsersIngestService",

    # Content & Questions
    "QuestionService",
    "QdrantService",

    # Excel & MCQ
    "ExcelService",
    "LinkTestWithPhoneService",
    "MCQService",
    "MCQScheduleService",
    "LeaderboardService",

    # Interview
    "InterviewLogicService",
    "InterviewRealtimeService",
    "InterviewSchedulerService",

    # User
    "UserMCQService",
    "UserTestService",
]
